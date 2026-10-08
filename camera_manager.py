import cv2
import threading

class CameraManager:
    def __init__(self, source=0):
        self.source = source
        self.cap = cv2.VideoCapture(self.source)
        self._lock = threading.Lock()

    def get_frame(self):
        with self._lock:
            if not self.cap.isOpened():
                self.cap.open(self.source)
            success, frame = self.cap.read()
        return success, frame

    def release(self):
        with self._lock:
            if self.cap.isOpened():
                self.cap.release()

camera_stream = CameraManager(0)