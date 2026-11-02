# Quản lý webcam máy chủ: một worker dùng chung, tự đóng khi người xem cuối cùng rời đi.
import atexit
import logging
import threading
import cv2

class CameraManager:
    """One lazy camera/recognition worker shared by all viewers."""
    def __init__(self, source=0):
        # Số 0 thường là webcam mặc định của máy chạy Python, không phải máy khách từ xa.
        self.source = source
        # Điều kiện đồng bộ để worker đánh thức các luồng HTTP khi có ảnh mới.
        self._condition = threading.Condition()
        # Khóa riêng cho thao tác mở/đóng, ngăn tạo hai worker cùng giữ camera.
        self._lifecycle = threading.Lock()
        # Số bộ sinh video đang có người xem trong phiên worker hiện tại.
        self._viewers = 0
        # Cờ dừng riêng cho mỗi phiên worker; tránh phiên cũ ảnh hưởng phiên mới.
        self._stop = threading.Event()
        self._worker = None
        # Giữ JPEG mới nhất để chia sẻ, không xếp hàng toàn bộ ảnh cũ.
        self._frame = None
        # Số thứ tự ảnh giúp mỗi người xem biết đã có khung hình mới hay chưa.
        self._sequence = 0

    # Thread nền đọc ảnh, gọi processor để nhận diện, rồi mã hóa ảnh kết quả thành JPEG.
    def _run(self, processor, stop):
        cap = None
        try:
            cap = cv2.VideoCapture(self.source)
            while not stop.is_set():
                success, frame = cap.read()
                # Camera đọc lỗi thì giải phóng, đợi một giây và thử mở lại nếu chưa có yêu cầu dừng.
                if not success:
                    cap.release()
                    if stop.wait(1):
                        break
                    cap.open(self.source)
                    continue
                # Chỉ xử lý nhận diện một lần cho mỗi ảnh trước khi gửi tới tất cả người xem.
                success, encoded = cv2.imencode('.jpg', processor(frame))
                if success:
                    with self._condition:
                        self._frame = encoded.tobytes()
                        self._sequence += 1
                        # Đánh thức các luồng đang đợi để nhận ảnh mới hoặc kết thúc khi camera dừng.
                        self._condition.notify_all()
                # Nghỉ ngắn có thể bị ngắt bởi cờ dừng; không phải cam kết tốc độ 30 FPS.
                stop.wait(0.03)
        except Exception:
            logging.exception('Lỗi xử lý camera')
        finally:
            # Luôn trả thiết bị lại cho hệ điều hành, kể cả khi xử lý ảnh gặp ngoại lệ.
            if cap is not None:
                cap.release()
            with self._condition:
                stop.set()
                # Đánh thức các luồng đang đợi để nhận ảnh mới hoặc kết thúc khi camera dừng.
                self._condition.notify_all()

    # Generator cung cấp từng JPEG cho một người xem; thân hàm bắt đầu chạy khi gọi next().
    def frames(self, processor):
        # Serialize opening and closing so a new viewer cannot reuse a worker
        # that is still releasing the physical camera.
        with self._lifecycle:
            if self._worker is not None and self._stop.is_set():
                # Đợi worker dừng, tối đa 3 giây; worker không cần khóa lifecycle nên có thể hoàn tất.
                self._worker.join(timeout=3)
                if self._worker.is_alive():
                    raise RuntimeError('Camera đang đóng, vui lòng thử lại.')
            with self._condition:
                if self._worker is None or not self._worker.is_alive():
                    # Cờ dừng riêng cho mỗi phiên worker; tránh phiên cũ ảnh hưởng phiên mới.
                    self._stop = threading.Event()
                    # Số bộ sinh video đang có người xem trong phiên worker hiện tại.
                    self._viewers = 0
                    # Giữ JPEG mới nhất để chia sẻ, không xếp hàng toàn bộ ảnh cũ.
                    self._frame = None
                    # Số thứ tự ảnh giúp mỗi người xem biết đã có khung hình mới hay chưa.
                    self._sequence = 0
                    self._worker = threading.Thread(
                        target=self._run, args=(processor, self._stop), daemon=True)
                    self._worker.start()
                # Giữ cờ của phiên này để việc đóng một response cũ không dừng nhầm phiên mới.
                stop = self._stop
                self._viewers += 1
                sequence = self._sequence
        try:
            while not stop.is_set():
                with self._condition:
                    self._condition.wait_for(
                        lambda: self._sequence != sequence or stop.is_set(), timeout=5)
                    if stop.is_set():
                        return
                    if self._sequence == sequence:
                        continue
                    sequence = self._sequence
                    frame = self._frame
                # Trả ảnh ngoài khóa condition để người xem chậm không chặn worker xuất bản ảnh mới.
                yield frame
        finally:
            with self._lifecycle:
                # An old response may close after a failed worker was replaced.
                # Chỉ giảm số người xem nếu response vẫn thuộc phiên camera hiện hành.
                if stop is self._stop:
                    with self._condition:
                        self._viewers -= 1
                        # Không còn người xem: yêu cầu worker đóng camera để trình duyệt đăng ký có thể sử dụng.
                        if self._viewers == 0:
                            stop.set()
                            # Đánh thức các luồng đang đợi để nhận ảnh mới hoặc kết thúc khi camera dừng.
                            self._condition.notify_all()
                    # Không còn người xem: yêu cầu worker đóng camera để trình duyệt đăng ký có thể sử dụng.
                    if self._viewers == 0:
                        # Đợi worker dừng, tối đa 3 giây; worker không cần khóa lifecycle nên có thể hoàn tất.
                        self._worker.join(timeout=3)

    # Dừng chủ động toàn bộ worker; cũng được gọi khi tiến trình Python thoát.
    def release(self):
        with self._lifecycle:
            with self._condition:
                self._stop.set()
                # Đánh thức các luồng đang đợi để nhận ảnh mới hoặc kết thúc khi camera dừng.
                self._condition.notify_all()
            if self._worker is not None:
                # Đợi worker dừng, tối đa 3 giây; worker không cần khóa lifecycle nên có thể hoàn tất.
                self._worker.join(timeout=3)

camera_stream = CameraManager(0)
# Đăng ký dọn thiết bị lúc Python kết thúc bình thường.
atexit.register(camera_stream.release)
