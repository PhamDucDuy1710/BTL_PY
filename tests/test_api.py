import os
import tempfile
import unittest
from unittest.mock import patch

import db_config
from recognize import FaceRecognizer


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.original_db = db_config.DB_PATH
        db_config.DB_PATH = os.path.join(cls.temp.name, 'test.db')
        with patch.dict(os.environ, {'ADMIN_PASSWORD': 'test-secret'}):
            with patch.object(FaceRecognizer, 'load_embeddings'):
                import api
        cls.api = api
        cls.api.app.config['TESTING'] = True

    @classmethod
    def tearDownClass(cls):
        db_config.DB_PATH = cls.original_db
        cls.temp.cleanup()

    def setUp(self):
        self.client = self.api.app.test_client()

    def login(self):
        with self.client.session_transaction() as session:
            session['admin'] = 'admin'

    def test_private_endpoints(self):
        for url in ['/api/access-logs', '/api/current-detected', '/static/snapshots/example.jpg']:
            self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.get('/video_feed').status_code, 302)

    def test_registration_template_exists(self):
        self.login()
        self.assertEqual(self.client.get('/register').status_code, 200)

    def test_reject_path_traversal_before_database_write(self):
        self.login()
        response = self.client.post('/api/students/register_face', json={
            'student_id': '../outside', 'full_name': 'Test', 'image': 'invalid'})
        self.assertEqual(response.status_code, 400)

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
