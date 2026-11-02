
    // Đồng hồ thời gian thực
    setInterval(() => {
      document.getElementById('liveClock').innerText = new Date().toLocaleString('vi-VN');
    }, 1000);

    // Giữ MediaStream để có thể stop các track khi đóng form hoặc bấm Tắt camera.
    let streamTracker = null;

    // Camera đăng ký thuộc máy đang mở trình duyệt, khác camera nhận diện của máy chủ.
    async function startWebcam() {
      try {
        // Xin quyền camera; có thể lỗi nếu thiết bị đang bị ứng dụng khác chiếm hoặc ngữ cảnh không cho phép.
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        // Gán luồng trực tiếp cho thẻ video để xem trước, chưa gửi ảnh lên server.
        document.getElementById('webcamVideo').srcObject = stream;
        streamTracker = stream;
      } catch (err) {
        alert("Không thể truy cập Webcam trình duyệt: " + err.message);
      }
    }

    function stopWebcam() {
      if (streamTracker) {
        // Dừng thiết bị thực sự; chỉ ẩn hộp thoại sẽ không tự giải phóng camera.
        streamTracker.getTracks().forEach(track => track.stop());
        streamTracker = null;
      }
    }

    // Hiện form và xin mở webcam ngay khi người dùng chọn thêm sinh viên.
    function openAddModal() {
      document.getElementById('addStudentModal').classList.add('active');
      startWebcam();
    }

    // Đóng form kèm giải phóng luồng camera của trình duyệt.
    function closeAddModal() {
      stopWebcam();
      document.getElementById('addStudentModal').classList.remove('active');
    }

    // Kiểm tra dữ liệu, chụp một khung hình rồi gửi ảnh kèm hồ sơ tới Flask.
    async function captureAndSubmit() {
      const student_id = document.getElementById('m_student_id').value.trim();
      const full_name = document.getElementById('m_full_name').value.trim();
      const class_id = document.getElementById('m_class_id').value.trim();

      if (!student_id || !full_name) {
        alert("Vui lòng nhập đầy đủ Mã sinh viên và Họ tên!");
        return;
      }

      const video = document.getElementById('webcamVideo');
      const canvas = document.getElementById('captureCanvas');
      if (!/^[A-Za-z0-9_-]{1,64}$/.test(student_id)) {
        alert('Mã sinh viên chỉ gồm chữ, số, dấu gạch dưới hoặc gạch ngang.');
        return;
      }
      // Chờ video có kích thước thật, tránh chụp canvas rỗng khi camera chưa sẵn sàng.
      if (!video.videoWidth || !streamTracker) {
        alert('Vui lòng bật camera và đợi hình ảnh trước khi chụp.');
        return;
      }
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight || 480;

      const ctx = canvas.getContext('2d');
      // Canvas sao chép khung hình hiện tại; thao tác này chính là chụp ảnh từ video.
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      // Mã hóa ảnh JPEG thành chuỗi Data URL để gửi trong JSON; 0,95 là mức chất lượng JPEG.
      const base64Image = canvas.toDataURL('image/jpeg', 0.95);

      const btn = document.getElementById('btnSnapAndSave');
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang kiểm tra và xử lý ảnh...`;

      try {
        // Máy chủ tiếp tục kiểm tra đầu vào; kiểm tra ở trình duyệt không thay thế kiểm tra phía server.
        const response = await fetch('/api/students/register_face', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: student_id,
            full_name: full_name,
            class_id: class_id,
            image: base64Image
          })
        });

        // Đọc thông báo sau khi server lưu ảnh và cập nhật đặc trưng xong.
        const result = await response.json();
        if (response.ok && result.success) {
          stopWebcam();
          closeAddModal();
          alert("✅ " + result.message);
          location.reload();
        } else {
          alert("❌ Lỗi: " + result.message);
        }
      } catch (err) {
        alert("❌ Lỗi kết nối máy chủ!");
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }

    // Yêu cầu xóa cả hồ sơ và dữ liệu nhận diện liên quan; hỏi lại trước thao tác xóa.
    async function deleteStudent(id) {
      if (!confirm(`Bạn có chắc muốn xóa sinh viên ${id}?`)) return;
      try {
        const res = await fetch(`/api/students/delete/${id}`, { method: 'DELETE' });
        if (res.ok) {
          alert("Đã xóa hoàn toàn sinh viên!");
          location.reload();
        } else {
          alert("Lỗi khi xóa sinh viên trên server!");
        }
      } catch (e) {
        alert("Lỗi khi gửi yêu cầu xóa!");
      }
    }

    // Lọc ngay các hàng đã có trên trang, không gửi truy vấn tìm kiếm tới CSDL.
    function filterTable() {
      const q = document.getElementById('searchInput').value.toLowerCase();
      const rows = document.querySelectorAll('#studentTableBody tr');
      rows.forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? '' : 'none';
      });
    }
  