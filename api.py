# Điểm chạy máy chủ Flask: giao diện, xác thực, quản lý dữ liệu và API nhận diện.
import os
import cv2
import sqlite3
import base64
import shutil
import pickle
import inspect
import threading
import traceback
import re
import secrets
import face_recognition
import numpy as np
from feature_store import FEATURE_LOCK, EMBEDDINGS_FILE, write_embeddings
from functools import wraps
from add_persons import serialized_training
from datetime import datetime
from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

from db_config import get_db_connection, init_db
from recognize import FaceRecognizer
from add_persons import extract_and_update_features
from camera_manager import camera_stream

# Khởi tạo CSDL lúc import mô đun; database mới cần ADMIN_PASSWORD.
init_db()

# Dự án đặt cả mẫu HTML Jinja và tài nguyên CSS/JS trong thư mục static.
app = Flask(__name__, template_folder='static', static_folder='static')
# Khóa ký cookie phiên đăng nhập; nếu sinh ngẫu nhiên thì đăng nhập cũ hết hiệu lực sau khi restart.
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
# Giới hạn request 6 MiB; HttpOnly chặn JavaScript đọc cookie, SameSite giảm gửi cookie chéo trang.
app.config.update(MAX_CONTENT_LENGTH=6 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tạo bộ nhận diện dùng chung và nạp vector; chưa mở webcam ở bước này.
recognizer = FaceRecognizer()

@app.before_request
# Chặn tải trực tiếp ảnh minh chứng nếu chưa có phiên quản trị.
def protect_snapshots():
    if request.path.startswith('/static/snapshots/') and 'admin' not in session:
        return jsonify(success=False, message='Chưa đăng nhập'), 401


# Decorator kiểm tra đăng nhập trước khi thực hiện hàm xử lý trang hoặc API.
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'admin' not in session:
            # API trả JSON và HTTP 401; trang HTML chuyển hướng về màn hình đăng nhập.
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper


# Nạp lại vector trong RAM sau khi cập nhật tệp, không cần khởi động lại server.
def reload_recognizer_memory():
    if hasattr(recognizer, 'load_known_faces'):
        recognizer.load_known_faces()
    elif hasattr(recognizer, 'load_embeddings'):
        recognizer.load_embeddings()


@serialized_training
# Loại cả vector và nhãn của người bị xóa, giữ nguyên thứ tự tương ứng của các mẫu còn lại.
def sync_pickle_after_deletion(deleted_student_id):
    emb_path = EMBEDDINGS_FILE
    if os.path.exists(emb_path):
        try:
            with open(emb_path, 'rb') as f:
                data = pickle.load(f)
            
            encs = data.get('encodings', [])
            ids = data.get('ids', [])
            
            new_encs, new_ids = [], []
            for e, sid in zip(encs, ids):
                if str(sid) != str(deleted_student_id):
                    new_encs.append(e)
                    new_ids.append(sid)
                    
            write_embeddings({'encodings': new_encs, 'ids': new_ids})
            
            reload_recognizer_memory()
        except Exception as err:
            print(f"[Cảnh báo] Lỗi đồng bộ pickle: {err}")


# Hàm tương thích chữ ký cũ/mới của bộ trích xuất; lỗi được in thay vì ném lại.
def safe_extract_features(student_id=None):
    try:
        sig = inspect.signature(extract_and_update_features)
        if 'target_student_id' in sig.parameters and student_id:
            extract_and_update_features(target_student_id=student_id)
        else:
            extract_and_update_features()
    except Exception as e:
        print(f"[Cảnh báo] Lỗi khi trích xuất vector: {e}")


# --- AUTHENTICATION & TÀI KHOẢN ---
@app.route('/')
# Trang gốc chọn đích dựa trên trạng thái đăng nhập.
def index():
    if 'admin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
# GET hiển thị form; POST đọc thông tin gửi lên và xác thực tài khoản.
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()

        if admin:
            db_pw = admin['password']
            is_valid = False
            try:
                # So mật khẩu nhập với giá trị băm đã lưu.
                is_valid = check_password_hash(db_pw, password)
            except Exception:
                is_valid = (db_pw == password)

            
            # Nhánh tương thích vẫn chấp nhận so văn bản trực tiếp; không phải mọi đường đăng nhập đều chỉ so hash.
            if is_valid or (db_pw == password):
                
                # Chuyển mật khẩu định dạng cũ sang băm khi đăng nhập thành công.
                if not db_pw.startswith(('scrypt:', 'pbkdf2:')):
                    new_hash = generate_password_hash(password)
                    conn.execute("UPDATE admins SET password = ? WHERE id = ?", (new_hash, admin['id']))
                    conn.commit()

                conn.close()
                # Lưu dấu đăng nhập vào phiên Flask đã ký; không lưu mật khẩu trong phiên.
                session['admin'] = username
                return redirect(url_for('dashboard'))

        conn.close()
        return render_template('login.html', error="Tên đăng nhập hoặc mật khẩu không chính xác!")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
@login_required
# Đăng ký thêm tài khoản quản trị; khác với API đăng ký khuôn mặt sinh viên.
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not password:
            return render_template('register.html', error="Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!")
        
        if password != confirm_password:
            return render_template('register.html', error="Mật khẩu xác nhận không khớp!")

        conn = get_db_connection()
        existing_user = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        
        if existing_user:
            conn.close()
            return render_template('register.html', error="Tên đăng nhập này đã tồn tại!")

        hashed_pw = generate_password_hash(password)
        conn.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        conn.close()

        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/logout')
# Xóa dấu đăng nhập trong phiên rồi chuyển về trang login.
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))



@app.route('/dashboard')
@login_required
# Tổng hợp số lớp, số sinh viên và số mã sinh viên khác nhau đã được ghi nhận trong ngày.
def dashboard():
    conn = get_db_connection()
    total_classes = conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    # DISTINCT tránh đếm lặp một người; điều kiện timestamp hỗ trợ bản ghi cũ chưa có date_only.
    checked_in = conn.execute("""
        SELECT COUNT(DISTINCT student_id) 
        FROM access_logs 
        WHERE date_only = ? OR timestamp LIKE ?
    """, (today_str, f"%{today_str}%")).fetchone()[0]
    
    # Số chưa được ghi nhận hôm nay, chưa đủ để kết luận vắng một buổi học.
    not_checked_in = max(0, total_students - checked_in)

    # LEFT JOIN giữ bản ghi lịch sử kể cả khi không tìm được hồ sơ sinh viên tương ứng.
    recent_logs = conn.execute("""
        SELECT a.student_id, s.full_name, s.class_id, a.timestamp, a.snapshot_path
        FROM access_logs a
        LEFT JOIN students s ON a.student_id = s.student_id
        ORDER BY a.id DESC LIMIT 10
    """.strip()).fetchall()

    conn.close()

    stats = {
        "classes": total_classes,
        "students": total_students,
        "checked_in": checked_in,
        "not_checked_in": not_checked_in
    }

    return render_template('dashboard.html', stats=stats, recent_logs=recent_logs)


@app.route('/students')
@login_required
# Đọc hồ sơ rồi truyền vào mẫu Jinja để tạo các hàng trong bảng sinh viên.
def students_page():
    conn = get_db_connection()
    students = conn.execute("SELECT student_id, full_name, class_id FROM students").fetchall()
    conn.close()
    return render_template('students.html', students=students)


@app.route('/classes')
@login_required
# Tải danh sách lớp cho trang quản lý.
def classes_page():
    conn = get_db_connection()
    classes = conn.execute("SELECT class_id, class_name FROM classes").fetchall()
    conn.close()
    return render_template('classes.html', classes=classes)


@app.route('/attendance')
@login_required
# Trả trang nhận diện; trình duyệt sẽ mở /video_feed và gọi các API cập nhật riêng.
def attendance():
    return render_template('attendance.html')


@app.route('/history')
@login_required
# Tải lịch sử và danh sách lớp; phần lọc trên trang thực hiện bằng JavaScript.
def history_page():
    conn = get_db_connection()
    logs = conn.execute("""
        SELECT a.id, a.student_id, s.full_name, s.class_id, a.timestamp, a.snapshot_path
        FROM access_logs a
        LEFT JOIN students s ON a.student_id = s.student_id
        ORDER BY a.id DESC
    """).fetchall()
    
    classes = conn.execute("SELECT class_id, class_name FROM classes").fetchall()
    conn.close()
    
    return render_template('history.html', logs=logs, classes=classes)



@app.route('/dataset_image/<student_id>/<filename>')
@login_required
# Phục vụ ảnh đăng ký sau đăng nhập; avatar.jpg đại diện bằng ảnh đầu tiên trong thư mục.
def get_dataset_image(student_id, filename):
    # Chỉ cho mã đơn giản để tránh đưa dấu phân cách hoặc ../ vào đường dẫn thư mục.
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', student_id):
        return '', 404
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datasets', 'data', student_id)
    if filename == 'avatar.jpg' and os.path.isdir(folder):
        photos = sorted(name for name in os.listdir(folder) if name.lower().endswith(('.jpg', '.jpeg', '.png')))
        if photos:
            filename = photos[0]
    return send_from_directory(folder, filename)



# Đóng gói từng JPEG thành các phần của luồng MJPEG để thẻ img hiển thị video.
def generate_frames():
    frames = camera_stream.frames(recognizer.process_frame)
    try:
        for frame_bytes in frames:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        # Khi HTTP ngắt, đóng generator con để giảm người xem và trả camera nếu đây là người cuối.
        frames.close()


@app.route('/video_feed')
@login_required
# Response dạng luồng gửi liên tục, boundary=frame khớp dấu phân tách trong generate_frames.
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/api/current-detected')
@login_required
# Trả thông tin người mới nhận diện, hoặc JSON null khi thông tin quá hạn.
def api_current_detected():
    return jsonify(recognizer.get_current_detected())


@app.route('/api/access-logs')
@login_required
# Trả tối đa 50 lượt mới nhất cho giao diện cập nhật định kỳ, không phải toàn bộ lịch sử.
def api_access_logs():
    conn = get_db_connection()
    logs = conn.execute("""
        SELECT a.id, a.student_id, s.full_name, s.class_id, a.timestamp, a.snapshot_path
        FROM access_logs a
        LEFT JOIN students s ON a.student_id = s.student_id
        ORDER BY a.id DESC LIMIT 50
    """.strip()).fetchall()
    conn.close()

    data = []
    # Đánh số hiển thị từ 1 và đổi đường dẫn ảnh sang dạng URL từ gốc website.
    for idx, row in enumerate(logs, 1):
        snap = row["snapshot_path"] or ""
        if snap and not snap.startswith("/"):
            snap = "/" + snap.replace("\\", "/")

        data.append({
            "id": row["id"],
            "stt": idx,
            "student_id": row["student_id"],
            "full_name": row["full_name"] or "Chưa cập nhật",
            "class_name": row["class_id"] or "N/A",
            "timestamp": row["timestamp"],
            "snapshot": snap
        })
    return jsonify(data)


@app.route('/api/train', methods=['POST'])
@login_required
# Quét lại toàn bộ ảnh, tạo đặc trưng và nạp lại RAM; không huấn luyện lại mạng nhận diện.
def api_train_features():
    try:
        msg = extract_and_update_features()
        reload_recognizer_memory()
        return jsonify({"success": True, "message": msg or "Đã huấn luyện dữ liệu hoàn tất!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/students/register_face', methods=['POST'])
@login_required
@serialized_training
# Đăng ký qua JSON: kiểm tra ảnh trước, lưu hồ sơ và ảnh, rồi cập nhật vector đồng bộ.
def register_face():
    try:
        # Đọc payload JSON từ fetch của trang students, gồm thông tin sinh viên và ảnh Base64.
        data = request.get_json(force=True)
        student_id = data.get('student_id', '').strip()
        full_name = data.get('full_name', '').strip()
        class_id = data.get('class_id', '').strip() or "CHUA_XAC_DINH"
        image_base64 = data.get('image', '')

        if not student_id or not full_name or not image_base64:
            return jsonify({"success": False, "message": "Vui lòng nhập đủ Mã SV, Tên và ảnh!"}), 400

        # Chỉ cho mã đơn giản để tránh đưa dấu phân cách hoặc ../ vào đường dẫn thư mục.
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', student_id):
            return jsonify(success=False, message='Mã sinh viên chỉ gồm chữ, số, dấu gạch dưới hoặc gạch ngang; tối đa 64 ký tự.'), 400
        if len(full_name) > 150 or len(class_id) > 100:
            return jsonify(success=False, message='Tên hoặc mã lớp quá dài.'), 400
        try:
            # Bỏ tiền tố data:image/...;base64, nếu ảnh được gửi dưới dạng Data URL.
            raw = image_base64.split(',', 1)[-1]
            image_bytes = base64.b64decode(raw, validate=True)
            # Base64 thành bytes, bytes thành mảng uint8, rồi giải mã thành ảnh BGR.
            image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            # Kiểm tra ảnh đọc được và không vượt 4 triệu pixel.
            if image is None or image.shape[0] * image.shape[1] > 4000000:
                raise ValueError('Ảnh không hợp lệ hoặc kích thước quá lớn.')
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # Ảnh đăng ký web phải có đúng một mặt để tránh gán nhãn nhầm người.
            if len(face_recognition.face_locations(rgb)) != 1:
                raise ValueError('Ảnh cần có đúng một khuôn mặt rõ nét.')
        except (ValueError, TypeError) as error:
            return jsonify(success=False, message=str(error)), 400

        conn = get_db_connection()
        conn.execute("INSERT OR IGNORE INTO classes (class_id, class_name) VALUES (?, ?)", 
                     (class_id, class_id))
        conn.execute("""
            INSERT INTO students (student_id, full_name, class_id) VALUES (?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET full_name = excluded.full_name, class_id = excluded.class_id
        """, (student_id, full_name, class_id))
        conn.commit()
        conn.close()

        # Hồ sơ đã commit trước bước lưu ảnh/vectorS; các thao tác này không cùng một giao dịch.
        save_dir = os.path.join(BASE_DIR, 'datasets', 'data', student_id)
        os.makedirs(save_dir, exist_ok=True)

        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]

        image_bytes = base64.b64decode(image_base64)
        # Hậu tố ngẫu nhiên giảm nguy cơ trùng tên khi chụp nhiều ảnh.
        file_path = os.path.join(save_dir, f"{student_id}_{secrets.token_hex(8)}.jpg")
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)

        
        # Chỉ xử lý lại ảnh của người vừa đăng ký, giữ nguyên các mẫu của người khác.
        def train_student(sid):
            extract_and_update_features(target_student_id=sid)
            reload_recognizer_memory()

        # Chạy đồng bộ: chỉ báo thành công sau khi cập nhật vector và nạp lại bộ nhận diện.
        train_student(student_id)

        return jsonify({
            "success": True, 
            "message": f"Đã lưu thông tin sinh viên {full_name}. Đã cập nhật đặc trưng khuôn mặt!"
        })

    except Exception as e:
        # In chi tiết lỗi vào terminal để phục vụ tìm lỗi phía máy chủ.
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500


@app.route('/api/students/delete/<student_id>', methods=['DELETE'])
@login_required
@serialized_training
# Xóa hồ sơ, lịch sử, ảnh đăng ký, vector và trạng thái nhận diện của sinh viên.
def delete_student(student_id):
    try:
        # Chỉ cho mã đơn giản để tránh đưa dấu phân cách hoặc ../ vào đường dẫn thư mục.
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', student_id):
            return jsonify(status='error', message='Mã sinh viên không hợp lệ.'), 400
        conn = get_db_connection()
        conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM access_logs WHERE student_id = ?", (student_id,))
        conn.commit()
        conn.close()

        for folder in ['datasets/data', 'datasets/new_persons']:
            p = os.path.join(BASE_DIR, folder, student_id)
            if os.path.exists(p):
                shutil.rmtree(p, ignore_errors=True)

        sync_pickle_after_deletion(student_id)
        # Bỏ mốc chống ghi lặp; None giúp không báo lỗi nếu chưa từng có mốc.
        recognizer.last_marked.pop(student_id, None)
        if recognizer.current_detected and recognizer.current_detected['student_id'] == student_id:
            recognizer.current_detected = None
        snapshot_dir = os.path.join(BASE_DIR, 'static', 'snapshots')
        for filename in os.listdir(snapshot_dir):
            if filename.startswith(student_id + '_') and filename.endswith('.jpg'):
                os.remove(os.path.join(snapshot_dir, filename))
        return jsonify({"status": "success", "message": f"Đã xóa triệt để sinh viên {student_id}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/classes/add', methods=['POST'])
@login_required
# Nhận FormData; nếu mã lớp đã có thì cập nhật tên, không xóa rồi tạo lại lớp.
def add_class():
    cid = request.form.get('class_id', '').strip()
    name = request.form.get('class_name', '').strip()
    if not cid or not name:
        return jsonify(success=False, message='Vui lòng nhập mã lớp và tên lớp.'), 400
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO classes (class_id, class_name) VALUES (?, ?) " 
        "ON CONFLICT(class_id) DO UPDATE SET class_name = excluded.class_name", 
        (cid, name))
    conn.commit()
    conn.close()
    return redirect(url_for('classes_page'))


@app.route('/api/classes/delete/<class_id>', methods=['DELETE'])
@login_required
# Kiểm tra còn sinh viên trước khi xóa lớp để không làm đứt liên kết dữ liệu.
def delete_class(class_id):
    conn = get_db_connection()
    
    student_count = conn.execute("SELECT COUNT(*) FROM students WHERE class_id = ?", (class_id,)).fetchone()[0]
    if student_count > 0:
        conn.close()
        return jsonify({
            "status": "error", 
            "message": f"Không thể xóa lớp: Vẫn còn {student_count} sinh viên thuộc lớp này!"
        }), 400

    conn.execute("DELETE FROM classes WHERE class_id = ?", (class_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})


if __name__ == '__main__':
    # Lắng nghe cổng 5001 trên các địa chỉ mạng của máy; debug=False nên sửa mã cần restart.
    app.run(host='0.0.0.0', port=5001, debug=False)
