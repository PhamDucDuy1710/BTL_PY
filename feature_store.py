"""Shared lock and atomic writes for face embeddings within one server process."""
import os
import pickle
import tempfile
import threading

FEATURE_LOCK = threading.RLock()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_FILE = os.path.join(BASE_DIR, 'datasets', 'face_features', 'embeddings.pickle')


def write_embeddings(data):
    os.makedirs(os.path.dirname(EMBEDDINGS_FILE), exist_ok=True)
    with FEATURE_LOCK:
        fd, temporary = tempfile.mkstemp(dir=os.path.dirname(EMBEDDINGS_FILE), suffix='.tmp')
        try:
            with os.fdopen(fd, 'wb') as stream:
                pickle.dump(data, stream)
            os.replace(temporary, EMBEDDINGS_FILE)
        finally:
            if os.path.exists(temporary):
                os.remove(temporary)
