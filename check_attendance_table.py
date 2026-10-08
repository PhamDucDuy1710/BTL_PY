from db_config import get_db_connection

def check_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    print("===== DANH SÁCH LỚP HỌC =====")
    for row in cur.execute("SELECT * FROM classes").fetchall():
        print(f"[{row['class_id']}] {row['class_name']}")

    print("\n===== DANH SÁCH SINH VIÊN =====")
    for row in cur.execute("SELECT * FROM students").fetchall():
        print(f"Mã: {row['student_id']} | Họ tên: {row['full_name']} | Lớp: {row['class_id']}")

    print("\n===== LỊCH SỬ ĐIỂM DANH (10 BẢN GHI MỚI NHẤT) =====")
    for row in cur.execute("SELECT * FROM access_logs ORDER BY id DESC LIMIT 10").fetchall():
        print(f"ID: {row['id']} | SV: {row['student_id']} | Thời gian: {row['timestamp']} | Ảnh: {row['snapshot_path']}")

    conn.close()

if __name__ == '__main__':
    check_tables()