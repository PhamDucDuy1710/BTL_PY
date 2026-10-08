import os
import cv2
import pickle
import numpy as np
import face_recognition
from datetime import datetime
from db_config import get_db_connection

EMBEDDINGS_FILE = os.path.join('datasets', 'face_features', 'embeddings.pickle')
SNAPSHOT_DIR = os.path.join('static', 'snapshots')
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

class FaceRecognizer:
    def __init__(self):
        self.known_encodings = []
        self.known_ids = []
        self.last_marked = {}       # {student_id: datetime}
        self.cooldown_sec = 60
        self.current_detected = None
        self.load_embeddings()

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
        return self.current_detected

    def get_student_info(self, student_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT student_id, full_name, class_id FROM students WHERE student_id = ?", (student_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"student_id": row['student_id'], "full_name": row['full_name'], "class_id": row['class_id']}
        return {"student_id": student_id, "full_name": "Chưa rõ", "class_id": "N/A"}

    def mark_attendance(self, student_id, frame, face_loc):
        now = datetime.now()
        info = self.get_student_info(student_id)
        time_str = now.strftime('%H:%M:%S - %d/%m/%Y')
        date_str = now.strftime('%d/%m/%Y')

        is_cooldown = False
        remaining = 0
        if student_id in self.last_marked:
            elapsed = (now - self.last_marked[student_id]).total_seconds()
            if elapsed < self.cooldown_sec:
                is_cooldown = True
                remaining = int(self.cooldown_sec - elapsed)

        if not is_cooldown:
            y1, x2, y2, x1 = face_loc
            h, w, _ = frame.shape
            p = 25
            snapshot = frame[max(0, y1-p):min(h, y2+p), max(0, x1-p):min(w, x2+p)]
            snap_name = f"{student_id}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            snap_path = os.path.join(SNAPSHOT_DIR, snap_name)
            cv2.imwrite(snap_path, snapshot)

            db_snap_path = f"static/snapshots/{snap_name}"

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO access_logs (student_id, timestamp, date_only, snapshot_path)
                VALUES (?, ?, ?, ?)
            """, (student_id, time_str, date_str, db_snap_path))
            conn.commit()
            conn.close()

            self.last_marked[student_id] = now
            info['status'] = f"Đã điểm danh (chờ {self.cooldown_sec}s)"
            info['time'] = time_str
        else:
            info['status'] = f"Đã điểm danh (chờ {remaining}s)"
            info['time'] = self.last_marked[student_id].strftime('%H:%M:%S - %d/%m/%Y')

        self.current_detected = info

    def process_frame(self, frame):
        if not self.known_encodings:
            return frame

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small, locations)

        for enc, loc in zip(encodings, locations):
            dists = face_recognition.face_distance(self.known_encodings, enc)

            if len(dists) > 0:
                
                id_min_dists = {}
                for sid, dist in zip(self.known_ids, dists):
                    if sid not in id_min_dists or dist < id_min_dists[sid]:
                        id_min_dists[sid] = dist

                sorted_candidates = sorted(id_min_dists.items(), key=lambda x: x[1])
                best_sid, top1 = sorted_candidates[0]
                
                
                is_confident = (top1 <= 0.52)

                
                if is_confident and len(sorted_candidates) >= 2:
                    top2 = sorted_candidates[1][1]
                    margin = top2 - top1
                    MIN_MARGIN = 0.05
                    if margin < MIN_MARGIN:
                        is_confident = False

                y1, x2, y2, x1 = [v * 4 for v in loc]

                if is_confident:
                    self.mark_attendance(best_sid, frame, (y1, x2, y2, x1))

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(frame, (x1, y1 - 28), (x2, y1), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, best_sid, (x1 + 6, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
                    cv2.putText(frame, "Khong xac dinh", (x1 + 6, y1 - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)

        return frame

recognizer_engine = FaceRecognizer()