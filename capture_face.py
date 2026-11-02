# Tiện ích chụp ảnh bằng cửa sổ OpenCV khi chạy trực tiếp; khác với đăng ký qua trình duyệt.
import os
import cv2
from db_config import get_db_connection

# Thu thông tin từ bàn phím, lưu hồ sơ và ảnh; chưa tự trích xuất vector.
def capture_new_person():
    student_id = input("Nhập Mã Sinh Viên: ").strip()
    full_name = input("Nhập Họ và Tên: ").strip()
    class_id = input("Nhập Lớp (vd CNTT-K65): ").strip()

    
    # Đường dẫn tương đối với thư mục chạy lệnh; nên chạy từ thư mục gốc dự án.
    save_dir = os.path.join('datasets', 'data', student_id)
    os.makedirs(save_dir, exist_ok=True)

    # Tạo lớp nếu thiếu và thêm/cập nhật hồ sơ trước khi bắt đầu chụp ảnh.
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO classes (class_id, class_name) VALUES (?, ?)", (class_id, class_id))
    cur.execute("""
        INSERT INTO students (student_id, full_name, class_id) VALUES (?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET full_name = excluded.full_name, class_id = excluded.class_id
    """, (student_id, full_name, class_id))
    conn.commit()
    conn.close()

    # Mở webcam máy hiện tại; cần đóng các ứng dụng khác đang giữ cùng thiết bị.
    cap = cv2.VideoCapture(0)
    count = len([f for f in os.listdir(save_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
    print("[*] Nhấn phím 'C' hoặc 'SPACE' để chụp ảnh (chụp từ 3-5 góc mặt). Nhấn 'Q' để hoàn tất.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Vẽ hướng dẫn lên bản sao để ảnh lưu không chứa dòng chữ hướng dẫn.
        display_frame = frame.copy()
        cv2.putText(display_frame, f"Da chup: {count} | SPACE: Chup | Q: Thoat", 
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Capture New Person", display_frame)

        # Đợi phím 1 mili giây, lấy mã phím 8 bit để so với C, Space hoặc Q.
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' ') or key == ord('c'):
            count += 1
            img_path = os.path.join(save_dir, f"{student_id}_{count}.jpg")
            # Lưu ảnh gốc theo số thứ tự; tiện ích này không kiểm tra ảnh có đúng một khuôn mặt.
            cv2.imwrite(img_path, frame)
            print(f"-> Đã lưu {img_path}")
        elif key == ord('q'):
            break

    # Giải phóng webcam rồi đóng các cửa sổ OpenCV.
    cap.release()
    cv2.destroyAllWindows()
    print(f"[*] Hoàn tất thu thập cho sinh viên {student_id}. Hãy chạy 'python add_persons.py' để cập nhật vector.")

if __name__ == '__main__':
    capture_new_person()