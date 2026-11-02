from pathlib import Path
import json

originals = {}
def annotate(path, intro, notes, marker='#'):
    p = Path(path)
    original = p.read_text(encoding='utf-8')
    originals[path] = original
    lines = original.splitlines(keepends=True)
    result = [marker + ' ' + intro + '\n'] if intro else []
    found = set()
    for line in lines:
        key = line.strip()
        if key in notes:
            indent = line[:len(line)-len(line.lstrip())]
            for text in notes[key].split('\n'):
                result.append(indent + marker + ' ' + text + '\n')
            found.add(key)
        result.append(line)
    missing = set(notes)-found
    if missing:
        raise ValueError((path, missing))
    p.write_text(''.join(result),encoding='utf-8')

annotate('recognize.py', 'Nhận diện từ webcam: so khớp đặc trưng, lưu lịch sử và vẽ kết quả lên ảnh.', {
 'def synchronized(func):':'Decorator khóa dữ liệu đặc trưng để không đọc trong lúc một thread khác đang cập nhật.',
 '@wraps(func)':'Giữ tên và thông tin hàm gốc khi bọc hàm bằng decorator.',
 'SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), \'static\', \'snapshots\')':'Đường dẫn dựa trên vị trí tệp Python, không phụ thuộc thư mục chạy lệnh.',
 'self.known_encodings = []':'Danh sách vector mẫu; một sinh viên có thể có nhiều vector từ nhiều ảnh.',
 'self.known_ids = []':'Mỗi phần tử cùng chỉ số với known_encodings cho biết mẫu thuộc sinh viên nào.',
 'self.last_marked = {}':'Ánh xạ mã sinh viên -> thời điểm lưu gần nhất; mất khi khởi động lại tiến trình.',
 'self.cooldown_sec = 60':'Khoảng chờ chống lưu liên tục, không phải quy tắc điểm danh theo buổi học.',
 'def load_embeddings(self):':'Nạp dữ liệu mẫu từ pickle; chỉ dùng tệp tin cậy do chính ứng dụng tạo.',
 "if getattr(self, 'last_seen', None) and (datetime.now() - self.last_seen).total_seconds() < 5:":'Chỉ giữ thông tin người vừa thấy trong 5 giây; quá hạn trả None cho API.',
 'def get_student_info(self, student_id):':'Tra hồ sơ theo mã; trả thông tin dự phòng nếu vector còn tồn tại nhưng hồ sơ không có.',
 'def mark_attendance(self, student_id, frame, face_loc):':'Ghi một lượt nhận diện nếu hết thời gian chờ, đồng thời cập nhật trạng thái giao diện.',
 "time_str = now.strftime('%H:%M:%S - %d/%m/%Y')":'Chuỗi hiển thị đầy đủ thời gian; date_str bên dưới dùng cho lọc theo ngày.',
 'elapsed = (now - self.last_marked[student_id]).total_seconds()':'Tính số giây đã qua từ lần lưu gần nhất của chính sinh viên này.',
 'y1, x2, y2, x1 = face_loc':'Thứ tự tọa độ của thư viện là trên, phải, dưới, trái.',
 'snapshot = frame[max(0, y1-p):min(h, y2+p), max(0, x1-p):min(w, x2+p)]':'Cắt khuôn mặt với lề 25 pixel; chặn tọa độ để không vượt biên ảnh.',
 "db_snap_path = f\"static/snapshots/{snap_name}\"":'CSDL lưu đường dẫn ảnh để trình duyệt tải, không lưu toàn bộ dữ liệu ảnh.',
 'self.last_marked[student_id] = now':'Chỉ cập nhật thời điểm sau khi đã lưu bản ghi; các lần trong khoảng chờ không thay đổi mốc.',
 'self.current_detected = info':'Thông tin này phục vụ API hiện tại ngay cả khi chưa được phép lưu thêm lượt.',
 'def process_frame(self, frame):':'Nhận một ảnh BGR từ OpenCV, trả lại ảnh có khung và nhãn nhận diện.',
 'if not self.known_encodings:':'Chưa có mẫu thì trả ảnh nguyên trạng, không có cơ sở để so khớp.',
 'small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)':'Giảm mỗi chiều còn 1/4, tương đương 1/16 số điểm ảnh cần xử lý.',
 'rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)':'OpenCV dùng BGR, còn face_recognition nhận ảnh RGB.',
 'locations = face_recognition.face_locations(rgb_small)':'Tìm vị trí khuôn mặt trước khi trích xuất vector đặc trưng cho từng vị trí.',
 'for enc, loc in zip(encodings, locations):':'Ghép từng vector với vị trí khuôn mặt tương ứng trong cùng khung hình.',
 'dists = face_recognition.face_distance(self.known_encodings, enc)':'Khoảng cách càng nhỏ thì đặc trưng càng gần nhau; đây không phải xác suất.',
 'id_min_dists = {}':'Gộp nhiều ảnh của một sinh viên thành một ứng viên với khoảng cách tốt nhất.',
 'sorted_candidates = sorted(id_min_dists.items(), key=lambda x: x[1])':'Sắp xếp tăng dần theo khoảng cách để chọn mã sinh viên gần nhất.',
 'is_confident = (top1 <= 0.52)':'Ngưỡng chấp nhận khoảng cách; 0,52 không có nghĩa độ chính xác 52%.',
 'if is_confident and len(sorted_candidates) >= 2:':'Chỉ so hạng nhất với hạng hai khi có ít nhất hai mã sinh viên khác nhau.',
 'MIN_MARGIN = 0.05':'Nếu hai ứng viên quá gần nhau, từ chối để tránh quyết định thiếu phân biệt.',
 'y1, x2, y2, x1 = [v * 4 for v in loc]':'Nhân 4 để đưa tọa độ từ ảnh thu nhỏ về kích thước ảnh gốc.',
 'cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)':'Vẽ khung xanh cho kết quả chấp nhận, rồi ghi mã sinh viên lên ảnh.',
 'cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)':'Khung vàng cho khuôn mặt chưa đủ điều kiện xác định.'
})

annotate('add_persons.py', 'Tạo dữ liệu đặc trưng từ ảnh đăng ký; dùng mô hình có sẵn, không huấn luyện lại mạng AI.', {
 'def serialized_training(func):':'Dùng chung khóa với bộ nhận diện để các lần cập nhật không ghi đè nhau.',
 'with FEATURE_LOCK:':'RLock cho phép cùng thread đi qua nhiều hàm đã khóa mà không tự khóa chính mình.',
 'def _load_existing_embeddings():':'Đọc hai danh sách song song: vector mẫu và mã sinh viên của từng vector.',
 'if target_student_id:':'Chế độ cập nhật một người: giữ mẫu người khác, thay toàn bộ mẫu cũ của người đang cập nhật.',
 'if str(sid) != str(target_student_id):':'Chỉ giữ vector không thuộc sinh viên cần xử lý lại.',
 'scan_targets = None':'None nghĩa là quét lại toàn bộ thư mục sinh viên và xây dựng lại danh sách mẫu.',
 'previous_count = len(known_encodings)':'Ghi số mẫu đã giữ để sau đó kiểm tra có tạo được mẫu mới cho sinh viên đích hay không.',
 'for student_id in (scan_targets if scan_targets is not None else os.listdir(DATA_DIR)):':'Mỗi thư mục con mang mã sinh viên, bên trong là các ảnh đăng ký.',
 'image = face_recognition.load_image_file(img_path)':'Đọc ảnh theo định dạng RGB mà thư viện nhận diện sử dụng.',
 'face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=2, model="hog")':'Thử bộ phát hiện HOG; phóng lớn ảnh trong bước tìm mặt để hỗ trợ mặt nhỏ.',
 'face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=3, model="hog")':'Nếu chưa tìm được mặt, thử tăng mức phóng lớn, đổi lại tốn thêm thời gian xử lý.',
 'face_locations = face_recognition.face_locations(image, number_of_times_to_upsample=1, model="cnn")':'Thử bộ phát hiện CNN dự phòng nếu các lần HOG không tìm được mặt.',
 'if len(face_locations) > 1:':'Ảnh nhập trực tiếp từ thư mục có thể nhiều mặt; chọn mặt lớn nhất. API web đã yêu cầu đúng một mặt.',
 'encs = face_recognition.face_encodings(image, known_face_locations=face_locations)':'Tạo vector số biểu diễn khuôn mặt tại vị trí vừa chọn.',
 'known_ids.append(student_id)':'Thêm nhãn cùng lúc với vector để bảo đảm hai danh sách luôn tương ứng theo chỉ số.',
 "write_embeddings({'encodings': known_encodings, 'ids': known_ids})":'Ghi qua tệp tạm và thay thế tệp đích để tránh đọc phải dữ liệu mới ghi một phần.',
 "if __name__ == '__main__':":'Chỉ quét toàn bộ khi chạy trực tiếp python add_persons.py; import không tự quét.'
})

annotate('camera_manager.py', 'Quản lý webcam máy chủ: một worker dùng chung, tự đóng khi người xem cuối cùng rời đi.', {
 'self.source = source':'Số 0 thường là webcam mặc định của máy chạy Python, không phải máy khách từ xa.',
 'self._condition = threading.Condition()':'Điều kiện đồng bộ để worker đánh thức các luồng HTTP khi có ảnh mới.',
 'self._lifecycle = threading.Lock()':'Khóa riêng cho thao tác mở/đóng, ngăn tạo hai worker cùng giữ camera.',
 'self._viewers = 0':'Số bộ sinh video đang có người xem trong phiên worker hiện tại.',
 'self._stop = threading.Event()':'Cờ dừng riêng cho mỗi phiên worker; tránh phiên cũ ảnh hưởng phiên mới.',
 'self._frame = None':'Giữ JPEG mới nhất để chia sẻ, không xếp hàng toàn bộ ảnh cũ.',
 'self._sequence = 0':'Số thứ tự ảnh giúp mỗi người xem biết đã có khung hình mới hay chưa.',
 'def _run(self, processor, stop):':'Thread nền đọc ảnh, gọi processor để nhận diện, rồi mã hóa ảnh kết quả thành JPEG.',
 'if not success:':'Camera đọc lỗi thì giải phóng, đợi một giây và thử mở lại nếu chưa có yêu cầu dừng.',
 "success, encoded = cv2.imencode('.jpg', processor(frame))":'Chỉ xử lý nhận diện một lần cho mỗi ảnh trước khi gửi tới tất cả người xem.',
 'self._condition.notify_all()':'Đánh thức các luồng đang đợi để nhận ảnh mới hoặc kết thúc khi camera dừng.',
 'stop.wait(0.03)':'Nghỉ ngắn có thể bị ngắt bởi cờ dừng; không phải cam kết tốc độ 30 FPS.',
 'if cap is not None:':'Luôn trả thiết bị lại cho hệ điều hành, kể cả khi xử lý ảnh gặp ngoại lệ.',
 'def frames(self, processor):':'Generator cung cấp từng JPEG cho một người xem; thân hàm bắt đầu chạy khi gọi next().',
 'self._worker.join(timeout=3)':'Đợi worker dừng, tối đa 3 giây; worker không cần khóa lifecycle nên có thể hoàn tất.',
 'stop = self._stop':'Giữ cờ của phiên này để việc đóng một response cũ không dừng nhầm phiên mới.',
 'yield frame':'Trả ảnh ngoài khóa condition để người xem chậm không chặn worker xuất bản ảnh mới.',
 'if stop is self._stop:':'Chỉ giảm số người xem nếu response vẫn thuộc phiên camera hiện hành.',
 'if self._viewers == 0:':'Không còn người xem: yêu cầu worker đóng camera để trình duyệt đăng ký có thể sử dụng.',
 'def release(self):':'Dừng chủ động toàn bộ worker; cũng được gọi khi tiến trình Python thoát.',
 'atexit.register(camera_stream.release)':'Đăng ký dọn thiết bị lúc Python kết thúc bình thường.'
})

annotate('db_config.py', 'Kết nối SQLite và khởi tạo cấu trúc dữ liệu dùng chung cho ứng dụng.', {
 'conn.row_factory = sqlite3.Row':"Cho phép đọc cột bằng tên, ví dụ row['student_id'], thay vì chỉ dùng chỉ số.",
 'conn.execute("PRAGMA foreign_keys = ON")':'Bật kiểm tra các khóa ngoại đã khai báo trên từng kết nối SQLite.',
 'def init_db():':'Tạo bảng nếu chưa có; không xóa dữ liệu đang tồn tại.',
 'cur = conn.cursor()':'Cursor thực thi câu SQL. Tham số ? được truyền riêng để không ghép dữ liệu vào câu lệnh.',
 "admin = cur.execute(\"SELECT * FROM admins WHERE username = 'admin'\").fetchone()":'Chỉ khởi tạo tài khoản admin khi chưa có, không ghi đè mật khẩu hiện tại.',
 "initial_password = os.environ.get('ADMIN_PASSWORD')":'Lấy mật khẩu khởi tạo từ môi trường thay vì ghi cứng trong mã nguồn.',
 'default_hash = generate_password_hash(initial_password)':'Lưu giá trị băm để không cần lưu mật khẩu mới dưới dạng văn bản rõ.',
 "cur.execute('CREATE INDEX IF NOT EXISTS idx_logs_date_student ON access_logs(date_only, student_id)')":'Chỉ mục hỗ trợ tra cứu theo ngày và sinh viên; không tạo ràng buộc duy nhất.',
 'conn.commit()':'Xác nhận các thay đổi vào CSDL trước khi đóng kết nối.'
})

annotate('feature_store.py', 'Kho đặc trưng dùng chung: khóa trong một tiến trình và ghi tệp theo cách thay thế nguyên tệp.', {
 'FEATURE_LOCK = threading.RLock()':'Khóa tái nhập: cùng thread được khóa lồng nhau; không đồng bộ giữa nhiều tiến trình server.',
 'def write_embeddings(data):':'Nhận dict chứa encodings và ids, lưu cùng nhau để không lệch vector và mã sinh viên.',
 "fd, temporary = tempfile.mkstemp(dir=os.path.dirname(EMBEDDINGS_FILE), suffix='.tmp')":'Tạo tệp tạm ngay trong thư mục đích để thao tác thay thế nằm trên cùng hệ thống tệp.',
 "with os.fdopen(fd, 'wb') as stream:":'Chuyển mô tả tệp thành luồng nhị phân; with tự đóng luồng sau khi ghi.',
 'os.replace(temporary, EMBEDDINGS_FILE)':'Chỉ thay tệp đích sau khi ghi hoàn tất, tránh để người đọc thấy tệp dở dang.',
 'if os.path.exists(temporary):':'Nếu có lỗi trước khi thay thế, xóa tệp tạm còn sót.'
})

annotate('capture_face.py', 'Tiện ích chụp ảnh bằng cửa sổ OpenCV khi chạy trực tiếp; khác với đăng ký qua trình duyệt.', {
 'def capture_new_person():':'Thu thông tin từ bàn phím, lưu hồ sơ và ảnh; chưa tự trích xuất vector.',
 "save_dir = os.path.join('datasets', 'data', student_id)":'Đường dẫn tương đối với thư mục chạy lệnh; nên chạy từ thư mục gốc dự án.',
 'conn = get_db_connection()':'Tạo lớp nếu thiếu và thêm/cập nhật hồ sơ trước khi bắt đầu chụp ảnh.',
 'cap = cv2.VideoCapture(0)':'Mở webcam máy hiện tại; cần đóng các ứng dụng khác đang giữ cùng thiết bị.',
 'display_frame = frame.copy()':'Vẽ hướng dẫn lên bản sao để ảnh lưu không chứa dòng chữ hướng dẫn.',
 'key = cv2.waitKey(1) & 0xFF':'Đợi phím 1 mili giây, lấy mã phím 8 bit để so với C, Space hoặc Q.',
 'cv2.imwrite(img_path, frame)':'Lưu ảnh gốc theo số thứ tự; tiện ích này không kiểm tra ảnh có đúng một khuôn mặt.',
 'cap.release()':'Giải phóng webcam rồi đóng các cửa sổ OpenCV.'
})

annotate('check_attendance_table.py', 'Tiện ích đọc nhanh dữ liệu từ SQLite trong terminal, không thay đổi các bản ghi.', {
 'def check_tables():':'In danh sách lớp, sinh viên và 10 lượt ghi nhận mới nhất.',
 'conn.close()':'Đóng kết nối sau khi đọc xong để trả tài nguyên cho SQLite.',
 "if __name__ == '__main__':":'Chỉ thực hiện khi chạy python check_attendance_table.py.'
})

annotate('api.py', 'Điểm chạy máy chủ Flask: giao diện, xác thực, quản lý dữ liệu và API nhận diện.', {
 'init_db()':'Khởi tạo CSDL lúc import mô đun; database mới cần ADMIN_PASSWORD.',
 "app = Flask(__name__, template_folder='static', static_folder='static')":'Dự án đặt cả mẫu HTML Jinja và tài nguyên CSS/JS trong thư mục static.',
 "app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)":'Khóa ký cookie phiên đăng nhập; nếu sinh ngẫu nhiên thì đăng nhập cũ hết hiệu lực sau khi restart.',
 "app.config.update(MAX_CONTENT_LENGTH=6 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')":'Giới hạn request 6 MiB; HttpOnly chặn JavaScript đọc cookie, SameSite giảm gửi cookie chéo trang.',
 'recognizer = FaceRecognizer()':'Tạo bộ nhận diện dùng chung và nạp vector; chưa mở webcam ở bước này.',
 'def protect_snapshots():':'Chặn tải trực tiếp ảnh minh chứng nếu chưa có phiên quản trị.',
 'def login_required(view_func):':'Decorator kiểm tra đăng nhập trước khi thực hiện hàm xử lý trang hoặc API.',
 "if request.path.startswith('/api/'):":'API trả JSON và HTTP 401; trang HTML chuyển hướng về màn hình đăng nhập.',
 'def reload_recognizer_memory():':'Nạp lại vector trong RAM sau khi cập nhật tệp, không cần khởi động lại server.',
 'def sync_pickle_after_deletion(deleted_student_id):':'Loại cả vector và nhãn của người bị xóa, giữ nguyên thứ tự tương ứng của các mẫu còn lại.',
 'def safe_extract_features(student_id=None):':'Hàm tương thích chữ ký cũ/mới của bộ trích xuất; lỗi được in thay vì ném lại.',
 'def index():':'Trang gốc chọn đích dựa trên trạng thái đăng nhập.',
 'def login():':'GET hiển thị form; POST đọc thông tin gửi lên và xác thực tài khoản.',
 'is_valid = check_password_hash(db_pw, password)':'So mật khẩu nhập với giá trị băm đã lưu.',
 'if is_valid or (db_pw == password):':'Nhánh tương thích vẫn chấp nhận so văn bản trực tiếp; không phải mọi đường đăng nhập đều chỉ so hash.',
 "if not db_pw.startswith(('scrypt:', 'pbkdf2:')):":'Chuyển mật khẩu định dạng cũ sang băm khi đăng nhập thành công.',
 "session['admin'] = username":'Lưu dấu đăng nhập vào phiên Flask đã ký; không lưu mật khẩu trong phiên.',
 'def register():':'Đăng ký thêm tài khoản quản trị; khác với API đăng ký khuôn mặt sinh viên.',
 'def logout():':'Xóa dấu đăng nhập trong phiên rồi chuyển về trang login.',
 'def dashboard():':'Tổng hợp số lớp, số sinh viên và số mã sinh viên khác nhau đã được ghi nhận trong ngày.',
 'checked_in = conn.execute("""':'DISTINCT tránh đếm lặp một người; điều kiện timestamp hỗ trợ bản ghi cũ chưa có date_only.',
 'not_checked_in = max(0, total_students - checked_in)':'Số chưa được ghi nhận hôm nay, chưa đủ để kết luận vắng một buổi học.',
 'recent_logs = conn.execute("""':'LEFT JOIN giữ bản ghi lịch sử kể cả khi không tìm được hồ sơ sinh viên tương ứng.',
 'def students_page():':'Đọc hồ sơ rồi truyền vào mẫu Jinja để tạo các hàng trong bảng sinh viên.',
 'def classes_page():':'Tải danh sách lớp cho trang quản lý.',
 'def attendance():':'Trả trang nhận diện; trình duyệt sẽ mở /video_feed và gọi các API cập nhật riêng.',
 'def history_page():':'Tải lịch sử và danh sách lớp; phần lọc trên trang thực hiện bằng JavaScript.',
 'def get_dataset_image(student_id, filename):':'Phục vụ ảnh đăng ký sau đăng nhập; avatar.jpg đại diện bằng ảnh đầu tiên trong thư mục.',
 'def generate_frames():':'Đóng gói từng JPEG thành các phần của luồng MJPEG để thẻ img hiển thị video.',
 'frames.close()':'Khi HTTP ngắt, đóng generator con để giảm người xem và trả camera nếu đây là người cuối.',
 'def video_feed():':'Response dạng luồng gửi liên tục, boundary=frame khớp dấu phân tách trong generate_frames.',
 'def api_current_detected():':'Trả thông tin người mới nhận diện, hoặc JSON null khi thông tin quá hạn.',
 'def api_access_logs():':'Trả tối đa 50 lượt mới nhất cho giao diện cập nhật định kỳ, không phải toàn bộ lịch sử.',
 'for idx, row in enumerate(logs, 1):':'Đánh số hiển thị từ 1 và đổi đường dẫn ảnh sang dạng URL từ gốc website.',
 'def api_train_features():':'Quét lại toàn bộ ảnh, tạo đặc trưng và nạp lại RAM; không huấn luyện lại mạng nhận diện.',
 'def register_face():':'Đăng ký qua JSON: kiểm tra ảnh trước, lưu hồ sơ và ảnh, rồi cập nhật vector đồng bộ.',
 'data = request.get_json(force=True)':'Đọc payload JSON từ fetch của trang students, gồm thông tin sinh viên và ảnh Base64.',
 "if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', student_id):":'Chỉ cho mã đơn giản để tránh đưa dấu phân cách hoặc ../ vào đường dẫn thư mục.',
 "raw = image_base64.split(',', 1)[-1]":'Bỏ tiền tố data:image/...;base64, nếu ảnh được gửi dưới dạng Data URL.',
 'image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)':'Base64 thành bytes, bytes thành mảng uint8, rồi giải mã thành ảnh BGR.',
 'if image is None or image.shape[0] * image.shape[1] > 4000000:':'Kiểm tra ảnh đọc được và không vượt 4 triệu pixel.',
 'if len(face_recognition.face_locations(rgb)) != 1:':'Ảnh đăng ký web phải có đúng một mặt để tránh gán nhãn nhầm người.',
 "save_dir = os.path.join(BASE_DIR, 'datasets', 'data', student_id)":'Hồ sơ đã commit trước bước lưu ảnh/vector; các thao tác này không cùng một giao dịch.',
 'file_path = os.path.join(save_dir, f"{student_id}_{secrets.token_hex(8)}.jpg")':'Hậu tố ngẫu nhiên giảm nguy cơ trùng tên khi chụp nhiều ảnh.',
 'def train_student(sid):':'Chỉ xử lý lại ảnh của người vừa đăng ký, giữ nguyên các mẫu của người khác.',
 'train_student(student_id)':'Chạy đồng bộ: chỉ báo thành công sau khi cập nhật vector và nạp lại bộ nhận diện.',
 'traceback.print_exc()':'In chi tiết lỗi vào terminal để phục vụ tìm lỗi phía máy chủ.',
 'def delete_student(student_id):':'Xóa hồ sơ, lịch sử, ảnh đăng ký, vector và trạng thái nhận diện của sinh viên.',
 'recognizer.last_marked.pop(student_id, None)':'Bỏ mốc chống ghi lặp; None giúp không báo lỗi nếu chưa từng có mốc.',
 'def add_class():':'Nhận FormData; nếu mã lớp đã có thì cập nhật tên, không xóa rồi tạo lại lớp.',
 'def delete_class(class_id):':'Kiểm tra còn sinh viên trước khi xóa lớp để không làm đứt liên kết dữ liệu.',
 "app.run(host='0.0.0.0', port=5001, debug=False)":'Lắng nghe cổng 5001 trên các địa chỉ mạng của máy; debug=False nên sửa mã cần restart.'
})

Path('tmp/comment-check/sources_before.json').write_text(json.dumps(originals,ensure_ascii=False),encoding='utf-8')
print('Annotated',len(originals),'Python files')
