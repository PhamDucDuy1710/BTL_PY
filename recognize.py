# Nhận diện từ webcam: so khớp đặc trưng, lưu lịch sử và vẽ kết quả lên ảnh.
import os
import cv2
import pickle
import numpy as np
import face_recognition
from datetime import datetime
from db_config import get_db_connection
from feature_store import FEATURE_LOCK, EMBEDDINGS_FILE
from functools import wraps

# Decorator khóa dữ liệu đặc trưng để không đọc trong lúc một thread khác đang cập nhật.
def synchronized(func):
    # Giữ tên và thông tin hàm gốc khi bọc hàm bằng decorator.
    @wraps(func)
    def wrapper(*args, **kwargs):
        with FEATURE_LOCK:
            return func(*args, **kwargs)
    return wrapper

# Đường dẫn dựa trên vị trí tệp Python, không phụ thuộc thư mục chạy lệnh.
SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), 'static', 'snapshots')
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

class FaceRecognizer:
    def __init__(self):
        # Danh sách vector mẫu; một sinh viên có thể có nhiều vector từ nhiều ảnh.
        self.known_encodings = []
        # Mỗi phần tử cùng chỉ số với known_encodings cho biết mẫu thuộc sinh viên nào.
        self.known_ids = []
        # Ánh xạ mã sinh viên -> thời điểm lưu gần nhất; mất khi khởi động lại tiến trình.
        self.last_marked = {}       
        # Khoảng chờ chống lưu liên tục, không phải quy tắc điểm danh theo buổi học.
        self.cooldown_sec = 60
        self.current_detected = None
        self.load_embeddings()

    @synchronized
    # Nạp dữ liệu mẫu từ pickle; chỉ dùng tệp tin cậy do chính ứng dụng tạo.
    def load_embeddings(self):
        if os.path.exists(EMBEDDINGS_FILE):
            try:
                with open(EMBEDDINGS_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.known_encodings = data.get('encodings', [])
                    self.known_ids = data.get('ids', [])
                print(f"[*] Đã nạp {len(self.known_encodings)} đặc trưng khuôn mặt.")
            except Exception as e:
                print(f"[!] Lỗi đọc file embeddings: {e}")
        else:
            print("[!] Chưa có file embeddings. Vui lòng chạy add_persons.py.")

    def load_known_faces(self):
        """Hỗ trợ nạp lại embedding tức thì khi bấm nút Training trên web"""
        self.load_embeddings()

    def get_current_detected(self):
        """Trả về thông tin người vừa quét cho API endpoint"""
        # Chỉ giữ thông tin người vừa thấy trong 5 giây; quá hạn trả None cho API.
        if getattr(self, 'last_seen', None) and (datetime.now() - self.last_seen).total_seconds() < 5:
            return self.current_detected
        return None

    # Tra hồ sơ theo mã; trả thông tin dự phòng nếu vector còn tồn tại nhưng hồ sơ không có.
    def get_student_info(self, student_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT student_id, full_name, class_id FROM students WHERE student_id = ?", (student_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"student_id": row['student_id'], "full_name": row['full_name'], "class_id": row['class_id']}
        return {"student_id": student_id, "full_name": "Chưa rõ", "class_id": "N/A"}

    # Ghi một lượt nhận diện nếu hết thời gian chờ, đồng thời cập nhật trạng thái giao diện.
    def mark_attendance(self, student_id, frame, face_loc):
        now = datetime.now()
        info = self.get_student_info(student_id)
        # Chuỗi hiển thị đầy đủ thời gian; date_str bên dưới dùng cho lọc theo ngày.
        time_str = now.strftime('%H:%M:%S - %d/%m/%Y')
        date_str = now.strftime('%d/%m/%Y')

        is_cooldown = False
        remaining = 0
        if student_id in self.last_marked:
            # Tính số giây đã qua từ lần lưu gần nhất của chính sinh viên này.
            elapsed = (now - self.last_marked[student_id]).total_seconds()
            if elapsed < self.cooldown_sec:
                is_cooldown = True
                remaining = int(self.cooldown_sec - elapsed)

        if not is_cooldown:
            # Thứ tự tọa độ của thư viện là trên, phải, dưới, trái.
            y1, x2, y2, x1 = face_loc
            h, w, _ = frame.shape
            p = 25
            # Cắt khuôn mặt với lề 25 pixel; chặn tọa độ để không vượt biên ảnh.
            snapshot = frame[max(0, y1-p):min(h, y2+p), max(0, x1-p):min(w, x2+p)]
            snap_name = f"{student_id}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            snap_path = os.path.join(SNAPSHOT_DIR, snap_name)
            cv2.imwrite(snap_path, snapshot)

            # CSDL lưu đường dẫn ảnh để trình duyệt tải, không lưu toàn bộ dữ liệu ảnh.
            db_snap_path = f"static/snapshots/{snap_name}"

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO access_logs (student_id, timestamp, date_only, snapshot_path)
                VALUES (?, ?, ?, ?)
            """, (student_id, time_str, date_str, db_snap_path))
            conn.commit()
            conn.close()

            # Chỉ cập nhật thời điểm sau khi đã lưu bản ghi; các lần trong khoảng chờ không thay đổi mốc.
            self.last_marked[student_id] = now
            info['status'] = f"Đã điểm danh (chờ {self.cooldown_sec}s)"
            info['time'] = time_str
        else:
            info['status'] = f"Đã điểm danh (chờ {remaining}s)"
            info['time'] = self.last_marked[student_id].strftime('%H:%M:%S - %d/%m/%Y')

        # Thông tin này phục vụ API hiện tại ngay cả khi chưa được phép lưu thêm lượt.
        self.current_detected = info
        self.last_seen = now

    @synchronized
    # Nhận một ảnh BGR từ OpenCV, trả lại ảnh có khung và nhãn nhận diện.
    def process_frame(self, frame):
        # Chưa có mẫu thì trả ảnh nguyên trạng, không có cơ sở để so khớp.
        if not self.known_encodings:
            return frame

        # Giảm mỗi chiều còn 1/4, tương đương 1/16 số điểm ảnh cần xử lý.
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        # OpenCV dùng BGR, còn face_recognition nhận ảnh RGB.
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Tìm vị trí khuôn mặt trước khi trích xuất vector đặc trưng cho từng vị trí.
        locations = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small, locations)

        # Ghép từng vector với vị trí khuôn mặt tương ứng trong cùng khung hình.
        for enc, loc in zip(encodings, locations):
            # Khoảng cách càng nhỏ thì đặc trưng càng gần nhau; đây không phải xác suất.
            dists = face_recognition.face_distance(self.known_encodings, enc)

            if len(dists) > 0:
                
                # Gộp nhiều ảnh của một sinh viên thành một ứng viên với khoảng cách tốt nhất.
                id_min_dists = {}
                for sid, dist in zip(self.known_ids, dists):
                    if sid not in id_min_dists or dist < id_min_dists[sid]:
                        id_min_dists[sid] = dist

                # Sắp xếp tăng dần theo khoảng cách để chọn mã sinh viên gần nhất.
                sorted_candidates = sorted(id_min_dists.items(), key=lambda x: x[1])
                best_sid, top1 = sorted_candidates[0]
                
                
                # Ngưỡng chấp nhận khoảng cách; 0,52 không có nghĩa độ chính xác 52%.
                is_confident = (top1 <= 0.52)

                
                # Chỉ so hạng nhất với hạng hai khi có ít nhất hai mã sinh viên khác nhau.
                if is_confident and len(sorted_candidates) >= 2:
                    top2 = sorted_candidates[1][1]
                    margin = top2 - top1
                    # Nếu hai ứng viên quá gần nhau, từ chối để tránh quyết định thiếu phân biệt.
                    MIN_MARGIN = 0.05
                    if margin < MIN_MARGIN:
                        is_confident = False

                # Nhân 4 để đưa tọa độ từ ảnh thu nhỏ về kích thước ảnh gốc.
                y1, x2, y2, x1 = [v * 4 for v in loc]

                if is_confident:
                    self.mark_attendance(best_sid, frame, (y1, x2, y2, x1))

                    # Vẽ khung xanh cho kết quả chấp nhận, rồi ghi mã sinh viên lên ảnh.
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(frame, (x1, y1 - 28), (x2, y1), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, best_sid, (x1 + 6, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
                else:
                    # Khung vàng cho khuôn mặt chưa đủ điều kiện xác định.
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
                    cv2.putText(frame, "Khong xac dinh", (x1 + 6, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)

        return frame
