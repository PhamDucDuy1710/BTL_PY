import os
import cv2
from db_config import get_db_connection

def capture_new_person():
    student_id = input("Nhập Mã Sinh Viên: ").strip()
    full_name = input("Nhập Họ và Tên: ").strip()
    class_id = input("Nhập Lớp (vd CNTT-K65): ").strip()

    
    save_dir = os.path.join('datasets', 'data', student_id)
    os.makedirs(save_dir, exist_ok=True)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO classes (class_id, class_name) VALUES (?, ?)", (class_id, class_id))
    cur.execute("""
        INSERT INTO students (student_id, full_name, class_id) VALUES (?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET full_name = excluded.full_name, class_id = excluded.class_id
    """, (student_id, full_name, class_id))
    conn.commit()
    conn.close()

    cap = cv2.VideoCapture(0)
    count = len([f for f in os.listdir(save_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
    print("[*] Nhấn phím 'C' hoặc 'SPACE' để chụp ảnh (chụp từ 3-5 góc mặt). Nhấn 'Q' để hoàn tất.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Da chup: {count} | SPACE: Chup | Q: Thoat", 
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Capture New Person", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' ') or key == ord('c'):
            count += 1
            img_path = os.path.join(save_dir, f"{student_id}_{count}.jpg")
            cv2.imwrite(img_path, frame)
            print(f"-> Đã lưu {img_path}")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"[*] Hoàn tất thu thập cho sinh viên {student_id}. Hãy chạy 'python add_persons.py' để cập nhật vector.")

if __name__ == '__main__':
    capture_new_person()