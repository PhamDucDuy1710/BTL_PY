# Điểm danh bằng nhận diện khuôn mặt

Ứng dụng Flask quản lý lớp, sinh viên và lịch sử nhận diện từ webcam.
Hiện ứng dụng ghi lịch sử ra/vào với khoảng chờ 60 giây cho mỗi sinh viên;
chưa có nghiệp vụ điểm danh riêng theo buổi học.

## Chạy trên Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:ADMIN_PASSWORD = 'nhap-mat-khau-quan-tri-cua-ban'
$env:FLASK_SECRET_KEY = 'nhap-chuoi-ngau-nhien-dai-va-giu-bi-mat'
python api.py
```

Mở http://localhost:5001. Database mới tạo tài khoản `admin` từ
`ADMIN_PASSWORD`. Database đã có tài khoản giữ nguyên mật khẩu hiện tại.
Nếu không đặt `FLASK_SECRET_KEY`, phiên đăng nhập hết hiệu lực khi khởi động lại.
`dlib` có thể yêu cầu CMake và bộ công cụ biên dịch C++ trên Windows.

## Đăng ký và nhận diện

Vào Quản lý sinh viên, nhập thông tin, bật webcam và chụp ảnh có đúng một
khuôn mặt rõ nét. Mã sinh viên chỉ gồm chữ ASCII, số, `_` hoặc `-`.
Ứng dụng kiểm tra ảnh và đợi cập nhật đặc trưng trước khi trả kết quả.
Nên bổ sung vài ảnh ở các góc và điều kiện sáng khác nhau cho mỗi sinh viên.

Camera và API lịch sử yêu cầu đăng nhập. Các cửa sổ video dùng chung một
luồng camera và nhận diện. Chạy một tiến trình server vì khóa cập nhật
embeddings chỉ đồng bộ các thread trong cùng tiến trình.

## Kiểm tra

```powershell
python -m unittest discover -s tests -v
node --check static/js/attendance.js
```

Ảnh, database và embeddings chứa dữ liệu cá nhân: không đưa dữ liệu thật
lên kho mã công khai. Cần bổ sung bảo vệ CSRF và cấu hình triển khai trước
khi cung cấp dịch vụ trên Internet.
