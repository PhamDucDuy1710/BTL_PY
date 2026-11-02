# Kết nối SQLite và khởi tạo cấu trúc dữ liệu dùng chung cho ứng dụng.
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'attendance.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    # Cho phép đọc cột bằng tên, ví dụ row['student_id'], thay vì chỉ dùng chỉ số.
    conn.row_factory = sqlite3.Row
    # Bật kiểm tra các khóa ngoại đã khai báo trên từng kết nối SQLite.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Tạo bảng nếu chưa có; không xóa dữ liệu đang tồn tại.
def init_db():
    conn = get_db_connection()
    # Cursor thực thi câu SQL. Tham số ? được truyền riêng để không ghép dữ liệu vào câu lệnh.
    cur = conn.cursor()

    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            class_id TEXT PRIMARY KEY,
            class_name TEXT NOT NULL
        )
    ''')

    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            class_id TEXT,
            FOREIGN KEY (class_id) REFERENCES classes(class_id)
        )
    ''')

   
    cur.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            date_only TEXT,
            snapshot_path TEXT
        )
    ''')

   
    # Chỉ khởi tạo tài khoản admin khi chưa có, không ghi đè mật khẩu hiện tại.
    admin = cur.execute("SELECT * FROM admins WHERE username = 'admin'").fetchone()
    if not admin:
        # Lấy mật khẩu khởi tạo từ môi trường thay vì ghi cứng trong mã nguồn.
        initial_password = os.environ.get('ADMIN_PASSWORD')
        if not initial_password:
            conn.close()
            raise RuntimeError('Database mới cần biến môi trường ADMIN_PASSWORD để tạo tài khoản admin.')
        # Lưu giá trị băm để không cần lưu mật khẩu mới dưới dạng văn bản rõ.
        default_hash = generate_password_hash(initial_password)
        cur.execute("INSERT INTO admins (username, password) VALUES ('admin', ?)", (default_hash,))

    # Chỉ mục hỗ trợ tra cứu theo ngày và sinh viên; không tạo ràng buộc duy nhất.
    cur.execute('CREATE INDEX IF NOT EXISTS idx_logs_date_student ON access_logs(date_only, student_id)')
    # Xác nhận các thay đổi vào CSDL trước khi đóng kết nối.
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()