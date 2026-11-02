import threading
import unittest
from unittest.mock import Mock, patch

from camera_manager import CameraManager


# Kiểm tra vòng đời thread bằng camera giả; không truy cập thiết bị thật.
class CameraManagerTests(unittest.TestCase):
    # Thay VideoCapture và mã hóa JPEG bằng mock để kiểm thử ổn định, độc lập phần cứng.
    def setUp(self):
        self.cameras = []

        def open_camera(source):
            camera = Mock()
            camera.read.return_value = (True, object())
            self.cameras.append(camera)
            return camera

        self.capture = patch('camera_manager.cv2.VideoCapture', side_effect=open_camera)
        self.encode = patch('camera_manager.cv2.imencode',
                            return_value=(True, Mock(tobytes=lambda: b'jpeg')))
        self.capture.start()
        self.encode.start()
        self.manager = CameraManager()
        self.streams = []

    # Đóng mọi generator và worker trước khi gỡ mock để không sót luồng nền.
    def tearDown(self):
        for stream in self.streams:
            stream.close()
        self.manager.release()
        self.capture.stop()
        self.encode.stop()

    # Tạo một người xem và gọi next để thực sự khởi chạy generator camera.
    def viewer(self, processor=lambda frame: frame):
        stream = self.manager.frames(processor)
        self.streams.append(stream)
        self.assertEqual(next(stream), b'jpeg')
        return stream

    # Kiểm tra người cuối đóng thì trả thiết bị, người mới vào thì mở camera mới.
    def test_last_viewer_releases_camera_and_can_reopen(self):
        first = self.viewer()
        first.close()
        self.cameras[0].release.assert_called_once()
        self.assertFalse(self.manager._worker.is_alive())
        self.viewer()
        self.assertEqual(len(self.cameras), 2)

    # Hai người cùng xem chỉ mở một camera; đóng một người không ngắt người còn lại.
    def test_closing_one_viewer_keeps_shared_camera_running(self):
        first = self.viewer()
        second = self.viewer()
        self.assertEqual(len(self.cameras), 1)
        first.close()
        self.cameras[0].release.assert_not_called()
        self.assertEqual(next(second), b'jpeg')
        second.close()
        self.cameras[0].release.assert_called_once()

    # Giả lập giải phóng chậm để kiểm tra người mới không mở thiết bị quá sớm.
    def test_new_viewer_waits_until_previous_camera_is_released(self):
        first = self.viewer()
        release_started = threading.Event()
        allow_release = threading.Event()

        def delayed_release():
            release_started.set()
            allow_release.wait(2)

        self.cameras[0].release.side_effect = delayed_release
        close_thread = threading.Thread(target=first.close)
        close_thread.start()
        self.assertTrue(release_started.wait(1))
        second = self.manager.frames(lambda frame: frame)
        self.streams.append(second)
        result = []
        open_started = threading.Event()

        def open_again():
            open_started.set()
            result.append(next(second))

        open_thread = threading.Thread(target=open_again)
        open_thread.start()
        try:
            self.assertTrue(open_started.wait(1))
            self.assertEqual(len(self.cameras), 1)
        finally:
            allow_release.set()
            close_thread.join(2)
            open_thread.join(2)
        self.assertFalse(open_thread.is_alive())
        self.assertEqual(result, [b'jpeg'])
        self.assertEqual(len(self.cameras), 2)

    # Response cũ đóng muộn không được làm giảm người xem hoặc dừng worker phiên mới.
    def test_closing_old_response_does_not_stop_replacement_worker(self):
        old = self.viewer()
        self.manager.release()
        current = self.viewer()
        old.close()
        self.cameras[1].release.assert_not_called()
        self.assertEqual(next(current), b'jpeg')

    # Ngay cả khi hàm nhận diện lỗi, camera vẫn phải được trả và có thể mở lại.
    def test_processing_error_releases_camera(self):
        stream = self.manager.frames(Mock(side_effect=ValueError('test error')))
        self.streams.append(stream)
        with self.assertLogs(level='ERROR'):
            with self.assertRaises(StopIteration):
                next(stream)
        self.cameras[0].release.assert_called_once()
        self.viewer()
        self.assertEqual(len(self.cameras), 2)


if __name__ == '__main__':
    unittest.main()
