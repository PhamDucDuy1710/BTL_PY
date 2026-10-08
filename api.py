import os
import cv2
import sqlite3
import base64
import shutil
import pickle
import inspect
import threading
import traceback
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

from db_config import get_db_connection, init_db
from recognize import FaceRecognizer
from add_persons import extract_and_update_features
from camera_manager import camera_stream

init_db()

app = Flask(__name__, template_folder='static', static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or 'super_secret_key_attendance_system_2026'

recognizer = FaceRecognizer()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'admin' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Chưa đăng nhập"}), 401
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper


def reload_recognizer_memory():
    if hasattr(recognizer, 'load_known_faces'):
        recognizer.load_known_faces()
    elif hasattr(recognizer, 'load_embeddings'):
        recognizer.load_embeddings()


def sync_pickle_after_deletion(deleted_student_id):
    emb_path = os.path.join('datasets', 'face_features', 'embeddings.pickle')
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
                    
            with open(emb_path, 'wb') as f:
                pickle.dump({'encodings': new_encs, 'ids': new_ids}, f)
            
            reload_recognizer_memory()
        except Exception as err:
            print(f"[Cảnh báo] Lỗi đồng bộ pickle: {err}")


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
def index():
    if 'admin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
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
                is_valid = check_password_hash(db_pw, password)
            except Exception:
                is_valid = (db_pw == password)

            
            if is_valid or (db_pw == password):
                
                if not db_pw.startswith(('scrypt:', 'pbkdf2:')):
                    new_hash = generate_password_hash(password)
                    conn.execute("UPDATE admins SET password = ? WHERE id = ?", (new_hash, admin['id']))
                    conn.commit()

                conn.close()
                session['admin'] = username
                return redirect(url_for('dashboard'))

        conn.close()
        return render_template('login.html', error="Tên đăng nhập hoặc mật khẩu không chính xác!")

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
@login_required
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
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))



@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    total_classes = conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    
    today_str = datetime.now().strftime("%d/%m/%Y")
    
    checked_in = conn.execute("""
        SELECT COUNT(DISTINCT student_id) 
        FROM access_logs 
        WHERE date_only = ? OR timestamp LIKE ?
    """, (today_str, f"%{today_str}%")).fetchone()[0]
    
    not_checked_in = max(0, total_students - checked_in)

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
def students_page():
    conn = get_db_connection()
    students = conn.execute("SELECT student_id, full_name, class_id FROM students").fetchall()
    conn.close()
    return render_template('students.html', students=students)


@app.route('/classes')
@login_required
def classes_page():
    conn = get_db_connection()
    classes = conn.execute("SELECT class_id, class_name FROM classes").fetchall()
    conn.close()
    return render_template('classes.html', classes=classes)


@app.route('/attendance')
def attendance():
    return render_template('attendance.html')


@app.route('/history')
@login_required
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
def get_dataset_image(student_id, filename):
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datasets', 'data', student_id)
    return send_from_directory(folder, filename)



def generate_frames():
    while True:
        success, frame = camera_stream.get_frame()
        if not success:
            break

        frame = recognizer.process_frame(frame)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/api/current-detected')
def api_current_detected():
    return jsonify(recognizer.get_current_detected())


@app.route('/api/access-logs')
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
    for idx, row in enumerate(logs, 1):
        snap = row["snapshot_path"] or ""
        if snap and not snap.startswith("/"):
            snap = "/" + snap.replace("\\", "/")

        data.append({
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
def api_train_features():
    try:
        msg = extract_and_update_features()
        reload_recognizer_memory()
        return jsonify({"success": True, "message": msg or "Đã huấn luyện dữ liệu hoàn tất!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/students/register_face', methods=['POST'])
@login_required
def register_face():
    try:
        data = request.get_json(force=True)
        student_id = data.get('student_id', '').strip()
        full_name = data.get('full_name', '').strip()
        class_id = data.get('class_id', '').strip() or "CHUA_XAC_DINH"
        image_base64 = data.get('image', '')

        if not student_id or not full_name or not image_base64:
            return jsonify({"success": False, "message": "Vui lòng nhập đủ Mã SV, Tên và ảnh!"}), 400

        conn = get_db_connection()
        conn.execute("INSERT OR IGNORE INTO classes (class_id, class_name) VALUES (?, ?)", 
                     (class_id, class_id))
        conn.execute("""
            INSERT INTO students (student_id, full_name, class_id) VALUES (?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET full_name = excluded.full_name, class_id = excluded.class_id
        """, (student_id, full_name, class_id))
        conn.commit()
        conn.close()

        save_dir = os.path.join('datasets', 'data', student_id)
        os.makedirs(save_dir, exist_ok=True)

        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]

        image_bytes = base64.b64decode(image_base64)
        file_count = len([f for f in os.listdir(save_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        file_path = os.path.join(save_dir, f"{student_id}_{file_count + 1}.jpg")
        
        with open(file_path, 'wb') as f:
            f.write(image_bytes)

        
        def background_train(sid):
            safe_extract_features(sid)
            reload_recognizer_memory()

        threading.Thread(target=background_train, args=(student_id,), daemon=True).start()

        return jsonify({
            "success": True, 
            "message": f"Đã lưu thông tin sinh viên {full_name}. Hệ thống đang trích xuất đặc trưng ngầm!"
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500


@app.route('/api/students/delete/<student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM access_logs WHERE student_id = ?", (student_id,))
        conn.commit()
        conn.close()

        for folder in ['datasets/data', 'datasets/new_persons']:
            p = os.path.join(folder, student_id)
            if os.path.exists(p):
                shutil.rmtree(p, ignore_errors=True)

        sync_pickle_after_deletion(student_id)
        return jsonify({"status": "success", "message": f"Đã xóa triệt để sinh viên {student_id}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/classes/add', methods=['POST'])
@login_required
def add_class():
    cid = request.form.get('class_id')
    name = request.form.get('class_name')
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO classes (class_id, class_name) VALUES (?, ?)", (cid, name))
    conn.commit()
    conn.close()
    return redirect(url_for('classes_page'))


@app.route('/api/classes/delete/<class_id>', methods=['DELETE'])
@login_required
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
    app.run(host='0.0.0.0', port=5001, debug=False)