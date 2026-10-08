import os
import pickle
import face_recognition

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'datasets', 'data')
FEATURES_DIR = os.path.join(BASE_DIR, 'datasets', 'face_features')
EMBEDDINGS_FILE = os.path.join(FEATURES_DIR, 'embeddings.pickle')

os.makedirs(FEATURES_DIR, exist_ok=True)

def _load_existing_embeddings():
    """Nạp embeddings.pickle hiện có (nếu có) để phục vụ cập nhật tăng dần."""
    if os.path.exists(EMBEDDINGS_FILE):
        try:
            with open(EMBEDDINGS_FILE, 'rb') as f:
                data = pickle.load(f)
                return list(data.get('encodings', [])), list(data.get('ids', []))
        except Exception as e:
            print(f"   [!] Không đọc được embeddings.pickle cũ, sẽ tạo mới: {e}")
    return [], []


def extract_and_update_features(target_student_id=None):
    """
    target_student_id=None  -> quét lại TOÀN BỘ DATA_DIR (dùng cho nút "Training" thủ công).
    target_student_id="SVxxx" -> CHỈ quét lại thư mục của sinh viên đó, giữ nguyên vector
                                  của tất cả sinh viên khác (chế độ tăng dần / incremental).
                                  Đây là chế độ nên dùng mỗi khi có 1 sinh viên vừa đăng ký
                                  ảnh mới qua web, để tránh phải quét lại hàng trăm ảnh cũ.
    """
    if target_student_id:
        prev_encodings, prev_ids = _load_existing_embeddings()
        known_encodings, known_ids = [], []
        for enc, sid in zip(prev_encodings, prev_ids):
            if str(sid) != str(target_student_id):
                known_encodings.append(enc)
                known_ids.append(sid)
        scan_targets = [target_student_id]
        print(f"[*] Chế độ tăng dần: chỉ xử lý lại sinh viên {target_student_id}")
    else:
        known_encodings, known_ids = [], []
        scan_targets = None  

    print(f"[*] Đang quét thư mục: {DATA_DIR}")
    if not os.path.exists(DATA_DIR):
        print("[!] Không tìm thấy thư mục data!")
        return

    for student_id in (scan_targets if scan_targets is not None else os.listdir(DATA_DIR)):
        student_folder = os.path.join(DATA_DIR, student_id)
        if os.path.isdir(student_folder):
            print(f"-> Đang xử lý sinh viên: {student_id}")
            for img_name in os.listdir(student_folder):
                if img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img_path = os.path.join(student_folder, img_name)
                    try:
                        image = face_recognition.load_image_file(img_path)

                        
                        face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2, model="hog")

                        if not face_locations:
                            face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=3, model="hog")
                        if not face_locations:
                            try:
                                face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1, model="cnn")
                            except Exception as e_cnn:
                                
                                print(f"   [i] Model CNN không khả dụng trên máy này ({e_cnn}), giữ nguyên kết quả HOG.")

                       
                        if len(face_locations) > 1:
                            print(f"   [!] Cảnh báo: {img_name} có {len(face_locations)} khuôn mặt, chỉ lấy mặt lớn nhất.")
                            
                            face_locations = [max(face_locations, key=lambda loc: (loc[2]-loc[0]) * (loc[1]-loc[3]))]

                        
                        encs = face_recognition.face_encodings(image, known_face_locations=face_locations)

                        if len(encs) > 0:
                            known_encodings.append(encs[0])
                            known_ids.append(student_id)
                            print(f"   [+] OK: {img_name} (Tìm thấy {len(encs)} mặt)")
                        else:
                            print(f"   [-] Không tìm thấy khuôn mặt: {img_name}")
                    except Exception as e:
                        print(f"   [!] Lỗi xử lý {img_name}: {e}")

    with open(EMBEDDINGS_FILE, 'wb') as f:
        pickle.dump({'encodings': known_encodings, 'ids': known_ids}, f)

    print(f"\n[*] Cập nhật đặc trưng thành công! Tổng số embeddings hiện tại: {len(known_encodings)}")

if __name__ == '__main__':
    extract_and_update_features()


#akdfasdkdf