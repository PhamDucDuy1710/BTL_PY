
    // Hiển thị thời gian máy khách theo định dạng tiếng Việt.
    function updateClock() {
      const d = new Date();
      document.getElementById('liveClock').innerText = d.toLocaleString('vi-VN');
    }
    setInterval(updateClock, 1000);
    updateClock();

    function openModal() { document.getElementById('addClassModal').classList.add('active'); }
    function closeModal() { document.getElementById('addClassModal').classList.remove('active'); }

    // TRƯỚC ĐÂY: form này submit truyền thống (tải lại cả trang), trong khi xóa lớp
    // lại dùng fetch() không tải lại trang -- 2 kiểu xử lý khác nhau cho cùng 1 trang.
    // GIỜ: dùng fetch() cho cả 2 thao tác để nhất quán. Gửi FormData (không phải JSON)
    // để KHÔNG cần sửa route /api/classes/add bên backend (vẫn đọc bằng request.form.get()).
    document.getElementById('addClassForm').addEventListener('submit', async (e) => {
      // Chặn submit mặc định để JavaScript chủ động gửi form bằng fetch.
      e.preventDefault();
      const form = e.target;
      const saveBtn = form.querySelector('.btn-save');
      const originalText = saveBtn.innerText;
      saveBtn.disabled = true;
      saveBtn.innerText = 'Đang lưu...';

      try {
        // FormData tương ứng request.form bên Flask; fetch mặc định theo chuyển hướng trả về.
        const res = await fetch('/api/classes/add', { method: 'POST', body: new FormData(form) });
        if (res.ok) {
          closeModal();
          form.reset();
          location.reload();
        } else {
          alert('Lỗi khi thêm lớp học!');
        }
      } catch (err) {
        alert('Lỗi kết nối máy chủ!');
      } finally {
        saveBtn.disabled = false;
        saveBtn.innerText = originalText;
      }
    });

    // So từ khóa không phân biệt hoa thường với văn bản của các hàng hiện có.
    function filterClasses() {
      const val = document.getElementById('searchInput').value.toLowerCase();
      const rows = document.querySelectorAll('#classesTableBody tr');
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(val) ? '' : 'none';
      });
    }

    // Gửi DELETE; server sẽ từ chối nếu lớp vẫn còn sinh viên.
    async function deleteClass(classId) {
      if (!confirm(`Bạn có chắc muốn xóa lớp ${classId}?`)) return;
      try {
        const res = await fetch(`/api/classes/delete/${classId}`, { method: 'DELETE' });
        if (res.ok) {
          alert("Đã xóa lớp học thành công!");
          location.reload();
        } else {
          alert("Lỗi khi xóa lớp học!");
        }
      } catch (err) {
        alert("Lỗi kết nối máy chủ!");
      }
    }
  