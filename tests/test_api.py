import os
import tempfile
import unittest
from unittest.mock import patch

import db_config
from recognize import FaceRecognizer


# Kiểm thử HTTP bằng Flask test client, không mở trình duyệt hoặc webcam thật.
class ApiTests(unittest.TestCase):
    @classmethod
    # Tạo CSDL tạm trước khi import api để init_db không ghi vào dữ liệu thật.
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.original_db = db_config.DB_PATH
        db_config.DB_PATH = os.path.join(cls.temp.name, 'test.db')
        with patch.dict(os.environ, {'ADMIN_PASSWORD': 'test-secret'}):
            # Bỏ qua nạp mẫu khuôn mặt vì các bài kiểm thử này tập trung vào API.
            with patch.object(FaceRecognizer, 'load_embeddings'):
                import api
        cls.api = api
        cls.api.app.config['TESTING'] = True

    @classmethod
    # Khôi phục đường dẫn CSDL và dọn thư mục tạm sau toàn bộ lớp kiểm thử.
    def tearDownClass(cls):
        db_config.DB_PATH = cls.original_db
        cls.temp.cleanup()

    # Mỗi ca kiểm thử có client mới để không dùng lại phiên đăng nhập của ca trước.
    def setUp(self):
        self.client = self.api.app.test_client()

    # Giả lập phiên đã đăng nhập, không kiểm tra thuật toán xác thực mật khẩu ở đây.
    def login(self):
        with self.client.session_transaction() as session:
            session['admin'] = 'admin'

    # Kiểm tra API/ảnh bị chặn và trang video chuyển tới login khi chưa đăng nhập.
    def test_private_endpoints(self):
        for url in ['/api/access-logs', '/api/current-detected', '/static/snapshots/example.jpg']:
            self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.get('/video_feed').status_code, 302)

    # Người chưa đăng nhập có thể mở form từ trang login.
    def test_registration_template_exists(self):
        self.assertEqual(self.client.get('/register').status_code, 200)
        self.assertIn(b'href="/register"', self.client.get('/login').data)

    def test_public_registration_and_login(self):
        response = self.client.post('/register', data={
            'username': 'public_test_admin', 'password': 'new-test-password',
            'confirm_password': 'new-test-password'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Tạo tài khoản quản trị thành công'.encode(), response.data)
        conn = db_config.get_db_connection()
        try:
            row = conn.execute("SELECT password FROM admins WHERE username = ?",
                               ('public_test_admin',)).fetchone()
            self.assertNotEqual(row['password'], 'new-test-password')
            self.assertTrue(self.api.check_password_hash(row['password'], 'new-test-password'))
        finally:
            conn.close()
        response = self.client.post('/login', data={
            'username': 'public_test_admin', 'password': 'new-test-password'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], '/dashboard')

    def test_public_registration_rejects_duplicate(self):
        response = self.client.post('/register', data={
            'username': 'admin', 'password': 'replacement',
            'confirm_password': 'replacement'})
        self.assertIn('Tên đăng nhập này đã tồn tại'.encode(), response.data)
        response = self.client.post('/login', data={
            'username': 'admin', 'password': 'test-secret'})
        self.assertEqual(response.headers['Location'], '/dashboard')

    def test_public_registration_rejects_mismatch(self):
        response = self.client.post('/register', data={
            'username': 'mismatch_admin', 'password': 'one',
            'confirm_password': 'two'})
        self.assertIn('Mật khẩu xác nhận không khớp'.encode(), response.data)
        conn = db_config.get_db_connection()
        try:
            self.assertIsNone(conn.execute(
                "SELECT id FROM admins WHERE username = 'mismatch_admin'").fetchone())
        finally:
            conn.close()

    # Dùng generator giả để kiểm tra đóng response cũng đóng đăng ký xem camera.
    def test_video_disconnect_closes_camera_subscription(self):
        self.login()
        closed = []

        def frames():
            try:
                while True:
                    yield b'jpeg'
            finally:
                closed.append(True)

        with patch.object(self.api.camera_stream, 'frames', return_value=frames()):
            response = self.client.get('/video_feed', buffered=False)
            self.assertIn(b'jpeg', next(iter(response.response)))
            response.close()
        self.assertEqual(closed, [True])

    # Mã chứa ../ phải bị từ chối trước khi tạo đường dẫn lưu ảnh.
    def test_reject_path_traversal_before_database_write(self):
        self.login()
        response = self.client.post('/api/students/register_face', json={
            'student_id': '../outside', 'full_name': 'Test', 'image': 'invalid'})
        self.assertEqual(response.status_code, 400)

    # Dữ liệu không phải ảnh phải trả lỗi và không để lại hồ sơ sinh viên.
    def test_invalid_image_does_not_create_student(self):
        self.login()
        response = self.client.post('/api/students/register_face', json={
            'student_id': 'INVALID_IMAGE', 'full_name': 'Test', 'image': 'aGVsbG8='})
        self.assertEqual(response.status_code, 400)
        conn = db_config.get_db_connection()
        try:
            self.assertIsNone(conn.execute("SELECT * FROM students WHERE student_id='INVALID_IMAGE'").fetchone())
        finally:
            conn.close()

    # Đổi tên lớp không được làm mất liên kết với sinh viên đang thuộc lớp.
    def test_update_class_with_students(self):
        self.login()
        conn = db_config.get_db_connection()
        try:
            conn.execute("INSERT INTO classes VALUES ('TEST_CLASS', 'Old name')")
            conn.execute("INSERT INTO students VALUES ('TEST_STUDENT', 'Student', 'TEST_CLASS')")
            conn.commit()
        finally:
            conn.close()
        response = self.client.post('/api/classes/add', data={'class_id': 'TEST_CLASS', 'class_name': 'New name'})
        self.assertEqual(response.status_code, 302)
        conn = db_config.get_db_connection()
        try:
            self.assertEqual(conn.execute("SELECT class_name FROM classes WHERE class_id='TEST_CLASS'").fetchone()[0], 'New name')
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()
