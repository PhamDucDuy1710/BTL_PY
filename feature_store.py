# Kho đặc trưng dùng chung: khóa trong một tiến trình và ghi tệp theo cách thay thế nguyên tệp.
"""Shared lock and atomic writes for face embeddings within one server process."""
import os
import pickle
import tempfile
import threading

# Khóa tái nhập: cùng thread được khóa lồng nhau; không đồng bộ giữa nhiều tiến trình server.
FEATURE_LOCK = threading.RLock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_FILE = os.path.join(BASE_DIR, 'datasets', 'face_features', 'embeddings.pickle')


# Nhận dict chứa encodings và ids, lưu cùng nhau để không lệch vector và mã sinh viên.
def write_embeddings(data):
    os.makedirs(os.path.dirname(EMBEDDINGS_FILE), exist_ok=True)
    with FEATURE_LOCK:
        # Tạo tệp tạm ngay trong thư mục đích để thao tác thay thế nằm trên cùng hệ thống tệp.
        fd, temporary = tempfile.mkstemp(dir=os.path.dirname(EMBEDDINGS_FILE), suffix='.tmp')
        try:
            # Chuyển mô tả tệp thành luồng nhị phân; with tự đóng luồng sau khi ghi.
            with os.fdopen(fd, 'wb') as stream:
                pickle.dump(data, stream)
            # Chỉ thay tệp đích sau khi ghi hoàn tất, tránh để người đọc thấy tệp dở dang.
            os.replace(temporary, EMBEDDINGS_FILE)
        finally:
            # Nếu có lỗi trước khi thay thế, xóa tệp tạm còn sót.
            if os.path.exists(temporary):
                os.remove(temporary)
