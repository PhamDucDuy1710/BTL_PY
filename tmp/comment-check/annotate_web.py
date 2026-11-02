from pathlib import Path
import json
from collections import defaultdict

snapshot=Path('tmp/comment-check/sources_before.json')
before=json.loads(snapshot.read_text(encoding='utf-8'))
def add(path, notes, prefix='//'):
    p=Path(path); source=p.read_text(encoding='utf-8')
    if path not in before:before[path]=source
    result=[];found=set()
    for line in source.splitlines(keepends=True):
        key=line.strip()
        if key in notes:
            indent=line[:len(line)-len(line.lstrip())]
            for note in notes[key].split('\n'):
                result.append(indent+prefix+' '+note+'\n')
            found.add(key)
        result.append(line)
    if set(notes)-found:raise ValueError((path,set(notes)-found))
    p.write_text(''.join(result),encoding='utf-8')

add('static/js/attendance.js',{
 'let lastLogSignature = null;':'Chuỗi JSON của lần tải trước để nhận biết nội dung lịch sử có thay đổi.',
 'let polling = false;':'Cờ chống chồng yêu cầu khi một lần gọi API mất hơn chu kỳ cập nhật một giây.',
 "window.addEventListener('pagehide', () => {":'Khi rời trang, ngắt kết nối ảnh MJPEG để máy chủ biết người xem đã đóng.',
 "if (video) video.src = 'data:,';":'Thay URL video bằng dữ liệu rỗng, không gọi endpoint dừng toàn bộ người xem khác.',
 'if (event.persisted) {':'Trang khôi phục từ bộ nhớ Back/Forward cần mở lại URL video đã ngắt.',
 'if (polling) return;':'Nếu lần tải trước chưa xong thì bỏ lượt này, tránh nhiều response về sai thứ tự.',
 'const student = await resCurrent.json();':'API trả một đối tượng sinh viên hoặc null khi không còn nhận diện gần đây.',
 'const signature = JSON.stringify(logs);':'So toàn bộ nội dung bản ghi, không chỉ số lượng; sửa thông tin cũng khiến bảng cập nhật.',
 'polling = false;':'Luôn trả cờ về trạng thái rảnh, kể cả khi tải API hoặc đọc JSON thất bại.',
 'setInterval(pollAttendanceState, 1000);':'Polling mỗi giây, độc lập với luồng video MJPEG trong thẻ img.',
 'pollAttendanceState();':'Tải ngay khi trang sẵn sàng, không chờ tới nhịp một giây đầu tiên.'
})
add('static/js/dashboard.js',{
 'function startClock() {':'Đồng hồ lấy giờ từ máy mở trình duyệt, không phải giờ được truy vấn từ máy chủ.',
 'function escapeHtml(value) {':'textContent coi đầu vào là văn bản; innerHTML trả lại dạng đã mã hóa dấu HTML.',
 'async function triggerFaceTraining() {':'Nút Training yêu cầu trích xuất lại vector từ ảnh, không huấn luyện mạng AI mới.',
 'btn.disabled = true;':'Vô hiệu nút trong lúc chờ để người dùng không bấm gửi lặp liên tục.',
 "const res = await fetch('/api/train', { method: 'POST' });":'await đợi máy chủ xử lý; cookie phiên cùng nguồn đi kèm yêu cầu để xác thực.',
 'btn.innerHTML = originalHtml;':'Khôi phục nhãn và trạng thái nút dù yêu cầu thành công hay thất bại.'
})
add('static/students.html',{
 'let streamTracker = null;':'Giữ MediaStream để có thể stop các track khi đóng form hoặc bấm Tắt camera.',
 'async function startWebcam() {':'Camera đăng ký thuộc máy đang mở trình duyệt, khác camera nhận diện của máy chủ.',
 'const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });':'Xin quyền camera; có thể lỗi nếu thiết bị đang bị ứng dụng khác chiếm hoặc ngữ cảnh không cho phép.',
 "document.getElementById('webcamVideo').srcObject = stream;":'Gán luồng trực tiếp cho thẻ video để xem trước, chưa gửi ảnh lên server.',
 'streamTracker.getTracks().forEach(track => track.stop());':'Dừng thiết bị thực sự; chỉ ẩn hộp thoại sẽ không tự giải phóng camera.',
 'function openAddModal() {':'Hiện form và xin mở webcam ngay khi người dùng chọn thêm sinh viên.',
 'function closeAddModal() {':'Đóng form kèm giải phóng luồng camera của trình duyệt.',
 'async function captureAndSubmit() {':'Kiểm tra dữ liệu, chụp một khung hình rồi gửi ảnh kèm hồ sơ tới Flask.',
 'if (!video.videoWidth || !streamTracker) {':'Chờ video có kích thước thật, tránh chụp canvas rỗng khi camera chưa sẵn sàng.',
 'ctx.drawImage(video, 0, 0, canvas.width, canvas.height);':'Canvas sao chép khung hình hiện tại; thao tác này chính là chụp ảnh từ video.',
 "const base64Image = canvas.toDataURL('image/jpeg', 0.95);":'Mã hóa ảnh JPEG thành chuỗi Data URL để gửi trong JSON; 0,95 là mức chất lượng JPEG.',
 "const response = await fetch('/api/students/register_face', {":'Máy chủ tiếp tục kiểm tra đầu vào; kiểm tra ở trình duyệt không thay thế kiểm tra phía server.',
 'const result = await response.json();':'Đọc thông báo sau khi server lưu ảnh và cập nhật đặc trưng xong.',
 'async function deleteStudent(id) {':'Yêu cầu xóa cả hồ sơ và dữ liệu nhận diện liên quan; hỏi lại trước thao tác xóa.',
 'function filterTable() {':'Lọc ngay các hàng đã có trên trang, không gửi truy vấn tìm kiếm tới CSDL.'
})
add('static/classes.html',{
 'function updateClock() {':'Hiển thị thời gian máy khách theo định dạng tiếng Việt.',
 'e.preventDefault();':'Chặn submit mặc định để JavaScript chủ động gửi form bằng fetch.',
 "const res = await fetch('/api/classes/add', { method: 'POST', body: new FormData(form) });":'FormData tương ứng request.form bên Flask; fetch mặc định theo chuyển hướng trả về.',
 'function filterClasses() {':'So từ khóa không phân biệt hoa thường với văn bản của các hàng hiện có.',
 'async function deleteClass(classId) {':'Gửi DELETE; server sẽ từ chối nếu lớp vẫn còn sinh viên.'
})
add('static/history.html',{
 'function updateClock() {':'Cập nhật đồng hồ máy khách, không thay đổi thời gian đã lưu trong lịch sử.',
 'function filterTable() {':'Kết hợp từ khóa mã/tên với lớp được chọn, chỉ ẩn/hiện các hàng đã tải.',
 'for (let i = 1; i < tr.length; i++) {':'Bỏ qua hàng tiêu đề ở chỉ số 0; hàng thông báo rỗng được bỏ qua nhờ kiểm tra các ô.',
 'tr[i].style.display = (matchText && matchClass) ? "" : "none";':'Một hàng chỉ hiển thị khi thỏa cả điều kiện từ khóa và điều kiện lớp.'
})
add('static/dashboard.html',{
 'function updateClock() {':'Chỉ cập nhật đồng hồ; các số thống kê trên trang do Flask tính lúc tải HTML.'
})

# Jinja comments are removed by the server and never appear as visible page content.
intros={
 'students':'Quản lý sinh viên: Flask tạo bảng ban đầu, JavaScript chụp ảnh và gọi API thêm/xóa.',
 'classes':'Quản lý lớp: dữ liệu classes từ Flask, form gửi tới API thêm hoặc cập nhật tên lớp.',
 'history':'Lịch sử nhận diện: dữ liệu logs từ Flask, bộ lọc chạy trong trình duyệt.',
 'dashboard':'Trang tổng quan: stats và recent_logs được máy chủ tính trước khi render.',
 'attendance':'Trang nhận diện: img nhận video MJPEG; JavaScript gọi API để cập nhật thông tin và bảng.',
 'login':'Form đăng nhập quản trị gửi POST tới Flask; biến error chứa thông báo lỗi nếu có.',
 'register':'Form tạo tài khoản quản trị mới, yêu cầu đã đăng nhập; không phải đăng ký khuôn mặt.'
}
for name, intro in intros.items():
    path=f'static/{name}.html';p=Path(path);source=p.read_text(encoding='utf-8')
    if path not in before:before[path]=source
    p.write_text('{# '+intro+' #}\n'+source,encoding='utf-8')

add('tests/test_api.py',{
 'class ApiTests(unittest.TestCase):':'Kiểm thử HTTP bằng Flask test client, không mở trình duyệt hoặc webcam thật.',
 'def setUpClass(cls):':'Tạo CSDL tạm trước khi import api để init_db không ghi vào dữ liệu thật.',
 "with patch.object(FaceRecognizer, 'load_embeddings'):":'Bỏ qua nạp mẫu khuôn mặt vì các bài kiểm thử này tập trung vào API.',
 'def tearDownClass(cls):':'Khôi phục đường dẫn CSDL và dọn thư mục tạm sau toàn bộ lớp kiểm thử.',
 'def setUp(self):':'Mỗi ca kiểm thử có client mới để không dùng lại phiên đăng nhập của ca trước.',
 'def login(self):':'Giả lập phiên đã đăng nhập, không kiểm tra thuật toán xác thực mật khẩu ở đây.',
 'def test_private_endpoints(self):':'Kiểm tra API/ảnh bị chặn và trang video chuyển tới login khi chưa đăng nhập.',
 'def test_registration_template_exists(self):':'Xác nhận trang tạo tài khoản render thành công cho người đã đăng nhập.',
 'def test_video_disconnect_closes_camera_subscription(self):':'Dùng generator giả để kiểm tra đóng response cũng đóng đăng ký xem camera.',
 'def test_reject_path_traversal_before_database_write(self):':'Mã chứa ../ phải bị từ chối trước khi tạo đường dẫn lưu ảnh.',
 'def test_invalid_image_does_not_create_student(self):':'Dữ liệu không phải ảnh phải trả lỗi và không để lại hồ sơ sinh viên.',
 'def test_update_class_with_students(self):':'Đổi tên lớp không được làm mất liên kết với sinh viên đang thuộc lớp.'
},'#')
add('tests/test_camera_manager.py',{
 'class CameraManagerTests(unittest.TestCase):':'Kiểm tra vòng đời thread bằng camera giả; không truy cập thiết bị thật.',
 'def setUp(self):':'Thay VideoCapture và mã hóa JPEG bằng mock để kiểm thử ổn định, độc lập phần cứng.',
 'def tearDown(self):':'Đóng mọi generator và worker trước khi gỡ mock để không sót luồng nền.',
 "def viewer(self, processor=lambda frame: frame):":'Tạo một người xem và gọi next để thực sự khởi chạy generator camera.',
 'def test_last_viewer_releases_camera_and_can_reopen(self):':'Kiểm tra người cuối đóng thì trả thiết bị, người mới vào thì mở camera mới.',
 'def test_closing_one_viewer_keeps_shared_camera_running(self):':'Hai người cùng xem chỉ mở một camera; đóng một người không ngắt người còn lại.',
 'def test_new_viewer_waits_until_previous_camera_is_released(self):':'Giả lập giải phóng chậm để kiểm tra người mới không mở thiết bị quá sớm.',
 'def test_closing_old_response_does_not_stop_replacement_worker(self):':'Response cũ đóng muộn không được làm giảm người xem hoặc dừng worker phiên mới.',
 'def test_processing_error_releases_camera(self):':'Ngay cả khi hàm nhận diện lỗi, camera vẫn phải được trả và có thể mở lại.'
},'#')

path='static/css/style.css';p=Path(path);before[path]=p.read_text(encoding='utf-8')
p.write_text('/* Kiểu giao diện dùng chung: màu sắc, bố cục và thành phần hiển thị; không xử lý dữ liệu nhận diện. */\n'+before[path],encoding='utf-8')
snapshot.write_text(json.dumps(before,ensure_ascii=False),encoding='utf-8')
print('Total annotated files:',len(before))
