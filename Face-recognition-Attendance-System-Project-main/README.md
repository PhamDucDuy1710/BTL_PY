# Face Recognition Attendance System

Hệ thống điểm danh bằng nhận diện khuôn mặt sử dụng **Python + OpenCV + face_recognition**.

## 1. Giới thiệu

Chương trình sử dụng webcam để phát hiện khuôn mặt, so sánh với các khuôn mặt đã đăng ký và tự động ghi nhận người đã được nhận diện vào file `Attendance.csv`.

Luồng hoạt động:

```text
Images_Attendance/
      ↓
Đọc ảnh mẫu
      ↓
Tạo Face Encoding
      ↓
Mở Webcam
      ↓
Đọc từng frame
      ↓
Phát hiện khuôn mặt
      ↓
Tạo Face Encoding
      ↓
So sánh với khuôn mặt đã đăng ký
      ↓
 ┌────┴────┐
 ↓         ↓
Khớp    Không khớp
 ↓         ↓
Tên      UNKNOWN
 ↓
Ghi điểm danh
 ↓
Attendance.csv
```

## 2. Cấu trúc project

```text
Face-recognition-Attendance-System/
│
├── AttendanceProject.py
├── Attendance.csv
├── README.md
│
└── Images_Attendance/
    ├── DucDuy.jpg
    ├── NguyenVanA.jpg
    └── TranVanB.jpg
```

### Ý nghĩa

| Thành phần | Chức năng |
|---|---|
| `AttendanceProject.py` | File chương trình chính, điều khiển toàn bộ hệ thống |
| `Images_Attendance/` | Chứa ảnh khuôn mặt của người đã đăng ký |
| `Attendance.csv` | Lưu tên, giờ và ngày điểm danh |
| `README.md` | Tài liệu hướng dẫn |

## 3. `Images_Attendance/` hoạt động như thế nào?

Đặt ảnh của từng người vào thư mục này.

Ví dụ:

```text
Images_Attendance/
├── DucDuy.jpg
├── NguyenVanA.jpg
└── TranVanB.jpg
```

Tên file được dùng làm tên người:

```text
DucDuy.jpg → DucDuy
```

Chương trình hỗ trợ:

- `.jpg`
- `.jpeg`
- `.png`
- `.bmp`
- `.webp`

Nên dùng ảnh rõ mặt và tốt nhất mỗi ảnh chỉ có một khuôn mặt.

## 4. `AttendanceProject.py` hoạt động như thế nào?

Đây là **file trung tâm** của project. Toàn bộ quá trình được thực hiện trong file này.

### Bước 1: Đọc ảnh mẫu

Hàm:

```python
load_known_images(PATH)
```

đọc các ảnh trong `Images_Attendance/`.

Kết quả gồm:

```text
images       → danh sách ảnh
class_names  → danh sách tên
```

Ví dụ:

```text
images[0]       ↔ class_names[0] = DucDuy
images[1]       ↔ class_names[1] = NguyenVanA
```

### Bước 2: Tạo Face Encoding

Hàm:

```python
find_encodings(images, class_names)
```

chuyển khuôn mặt trong ảnh thành **face encoding**.

Có thể hiểu:

```text
Ảnh khuôn mặt
      ↓
Face Encoding
      ↓
Dữ liệu số đại diện cho đặc điểm khuôn mặt
```

Các encoding được lưu trong:

```python
encode_list_known
```

Tên tương ứng nằm trong:

```python
class_names
```

### Bước 3: Mở webcam

```python
cap = cv2.VideoCapture(0)
```

`0` thường đại diện cho webcam mặc định.

Sau đó chương trình liên tục đọc frame:

```python
success, img = cap.read()
```

### Bước 4: Thu nhỏ frame

```python
FRAME_SCALE = 0.25
```

Frame camera được thu nhỏ còn 25%.

Mục đích là giảm lượng dữ liệu cần xử lý và giúp nhận diện nhanh hơn.

### Bước 5: Phát hiện khuôn mặt

```python
face_recognition.face_locations(rgb_small)
```

Tìm vị trí các khuôn mặt trong frame.

Sau đó:

```python
face_recognition.face_encodings(...)
```

tạo encoding cho từng khuôn mặt tìm được.

### Bước 6: So sánh

Chương trình tính khoảng cách:

```python
face_recognition.face_distance(
    encode_list_known,
    encode_face
)
```

Khoảng cách càng nhỏ thì khuôn mặt càng giống.

Sau đó:

```python
match_index = np.argmin(face_dis)
```

tìm khuôn mặt mẫu có khoảng cách nhỏ nhất.

### Bước 7: Quyết định có nhận diện hay không

Cấu hình:

```python
TOLERANCE = 0.50
```

Điều kiện:

```python
if distance <= TOLERANCE:
```

Nghĩa là:

```text
distance <= 0.50 → nhận diện người
distance >  0.50 → UNKNOWN
```

### Bước 8: Hiển thị kết quả

Nếu khớp:

```text
DUC DUY
```

và khung khuôn mặt màu xanh được hiển thị.

Nếu không khớp:

```text
UNKNOWN
```

và khung màu đỏ được hiển thị.

### Bước 9: Ghi điểm danh

Khi nhận diện được người, chương trình gọi:

```python
mark_attendance(name)
```

Nếu `Attendance.csv` chưa tồn tại, chương trình tạo file:

```text
Name,Time,Date
```

Ví dụ:

```text
Name,Time,Date
DUCDUY,08:15:32,21/08/2026
NGUYENVANA,08:16:05,21/08/2026
```

## 5. Các hàm chính

```text
AttendanceProject.py
│
├── load_known_images()
│      └── Đọc ảnh + lấy tên
│
├── find_encodings()
│      └── Tạo face encoding
│
├── mark_attendance()
│      └── Ghi điểm danh vào CSV
│
└── main()
       ├── Đọc ảnh
       ├── Tạo encoding
       ├── Mở webcam
       ├── Nhận diện
       ├── So sánh
       ├── Hiển thị
       └── Ghi điểm danh
```

## 6. Mối quan hệ giữa các file

```text
                 ẢNH MẪU
                    │
                    ↓
        ┌──────────────────────┐
        │ Images_Attendance/   │
        └──────────┬───────────┘
                   │
                   │ đọc ảnh
                   ↓
        ┌──────────────────────┐
        │ AttendanceProject.py │
        │                      │
        │ Face Encoding        │
        │ Webcam               │
        │ Face Detection       │
        │ Face Comparison      │
        └──────────┬───────────┘
                   │
                   │ kết quả nhận diện
                   ↓
        ┌──────────────────────┐
        │    Attendance.csv    │
        └──────────────────────┘
```

Nói ngắn gọn:

- `Images_Attendance/` = **dữ liệu đầu vào**
- `AttendanceProject.py` = **bộ xử lý**
- Webcam = **dữ liệu trực tiếp**
- `Attendance.csv` = **kết quả đầu ra**
- `README.md` = **tài liệu hướng dẫn**

## 7. Cách cài thư viện

```bash
pip install opencv-python
pip install numpy
pip install face-recognition
```

Kiểm tra Python:

```bash
python --version
```

## 8. Cách chạy

### Bước 1

Tạo thư mục:

```text
Images_Attendance
```

### Bước 2

Đưa ảnh khuôn mặt vào thư mục.

Ví dụ:

```text
Images_Attendance/DucDuy.jpg
Images_Attendance/NguyenVanA.jpg
```

### Bước 3

Chạy:

```bash
python AttendanceProject.py
```

### Bước 4

Đưa khuôn mặt trước webcam.

Nếu khớp với ảnh đã đăng ký:

```text
DUC DUY
```

Nếu không khớp:

```text
UNKNOWN
```

### Bước 5

Kết quả điểm danh được lưu vào:

```text
Attendance.csv
```

## 9. Chống điểm danh trùng

Hàm `mark_attendance()` kiểm tra tên đã tồn tại trong `Attendance.csv` hay chưa.

Nếu tên đã có:

```text
Không ghi thêm
```

Nếu chưa có:

```text
Ghi Name + Time + Date
```

**Lưu ý:** logic hiện tại kiểm tra tên trên toàn bộ file CSV. Vì vậy một người đã từng có tên trong file có thể không được ghi lại ở lần chạy sau. Nếu muốn điểm danh lại theo từng ngày, cần sửa điều kiện để kiểm tra cả **tên và ngày**.

## 10. Các phím điều khiển

Trong cửa sổ camera:

```text
ENTER → thoát
ESC   → thoát
```

Khi thoát:

```python
cap.release()
cv2.destroyAllWindows()
```

được gọi để giải phóng webcam và đóng cửa sổ.

## 11. Cấu hình quan trọng

### Thư mục ảnh

```python
PATH = "Images_Attendance"
```

### File điểm danh

```python
ATTENDANCE_FILE = "Attendance.csv"
```

### Độ chính xác nhận diện

```python
TOLERANCE = 0.50
```

### Tốc độ xử lý

```python
FRAME_SCALE = 0.25
```

## 12. Lỗi thường gặp

### Không tìm thấy `Images_Attendance`

Tạo thư mục:

```text
Images_Attendance/
```

và đặt ảnh vào đó.

### Ảnh không có khuôn mặt

Chương trình sẽ bỏ qua ảnh và báo:

```text
[WARNING] Không tìm thấy khuôn mặt trong ảnh
```

Hãy sử dụng ảnh rõ mặt hơn.

### Không mở được camera

Nếu thấy:

```text
[ERROR] Không thể mở camera.
```

hãy kiểm tra webcam và quyền truy cập camera.

### Nhận diện sai

Có thể điều chỉnh:

```python
TOLERANCE = 0.50
```

Giá trị thấp hơn thường làm điều kiện khớp nghiêm ngặt hơn.

## 13. Tóm tắt toàn bộ hệ thống

```text
Ảnh người đã đăng ký
        ↓
Images_Attendance/
        ↓
load_known_images()
        ↓
find_encodings()
        ↓
Danh sách Face Encoding
        ↓
Mở Webcam
        ↓
Đọc frame
        ↓
Phát hiện khuôn mặt
        ↓
Tạo Face Encoding
        ↓
face_distance()
        ↓
So sánh với TOLERANCE
        ↓
 ┌───────────────┐
 │               │
 KHỚP         KHÔNG KHỚP
 │               │
 ↓               ↓
Tên            UNKNOWN
 │
 ↓
mark_attendance()
 │
 ↓
Attendance.csv
```

## 14. Kết luận

Project gồm một file Python chính xử lý toàn bộ logic. Ảnh trong `Images_Attendance/` đóng vai trò dữ liệu khuôn mặt đã đăng ký. Webcam cung cấp dữ liệu khuôn mặt thực tế, sau đó `AttendanceProject.py` phát hiện và so sánh khuôn mặt. Nếu nhận diện thành công, thông tin được ghi vào `Attendance.csv`.

