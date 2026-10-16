import atexit
import logging
import threading
import cv2

class CameraManager:
    """One lazy camera/recognition worker shared by all viewers."""
    def __init__(self, source=0):
        self.source = source
        self._condition = threading.Condition()
        self._stop = threading.Event()
        self._worker = None
        self._frame = None
        self._sequence = 0

    def _run(self, processor):
        cap = cv2.VideoCapture(self.source)
        try:
            while not self._stop.is_set():
                success, frame = cap.read()
                if not success:
                    cap.release()
                    if self._stop.wait(1):
                        break
                    cap.open(self.source)
                    continue
                success, encoded = cv2.imencode('.jpg', processor(frame))
                if success:
                    with self._condition:
                        self._frame = encoded.tobytes()
                        self._sequence += 1
                        self._condition.notify_all()
                self._stop.wait(0.03)
        except Exception:
            logging.exception('Lỗi xử lý camera')
        finally:
            cap.release()
            with self._condition:
                self._stop.set()
                self._condition.notify_all()

    def frames(self, processor):
        with self._condition:
            if self._worker is None or not self._worker.is_alive():
                self._stop.clear()
                self._worker = threading.Thread(target=self._run, args=(processor,), daemon=True)
                self._worker.start()
            sequence = self._sequence
        while not self._stop.is_set():
            with self._condition:
                self._condition.wait_for(lambda: self._sequence != sequence or self._stop.is_set(), timeout=5)
                if self._stop.is_set():
                    return
                if self._sequence == sequence:
                    continue
                sequence = self._sequence
                frame = self._frame
            yield frame

    def release(self):
        self._stop.set()
        with self._condition:
            self._condition.notify_all()
        if self._worker is not None:
            self._worker.join(timeout=3)

camera_stream = CameraManager(0)
atexit.register(camera_stream.release)
