
    // Cập nhật đồng hồ máy khách, không thay đổi thời gian đã lưu trong lịch sử.
    function updateClock() {
      const d = new Date();
      document.getElementById('liveClock').innerText = d.toLocaleString('vi-VN');
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Kết hợp từ khóa mã/tên với lớp được chọn, chỉ ẩn/hiện các hàng đã tải.
    function filterTable() {
      const input = document.getElementById("searchInput").value.toUpperCase();
      const classVal = document.getElementById("classFilter").value.toUpperCase();
      const tr = document.getElementById("historyTable").getElementsByTagName("tr");

      // Bỏ qua hàng tiêu đề ở chỉ số 0; hàng thông báo rỗng được bỏ qua nhờ kiểm tra các ô.
      for (let i = 1; i < tr.length; i++) {
        const tdId = tr[i].getElementsByTagName("td")[2];
        const tdName = tr[i].getElementsByTagName("td")[3];
        const tdClass = tr[i].getElementsByTagName("td")[4];
        if (tdId && tdName && tdClass) {
          const txtId = tdId.textContent || tdId.innerText;
          const txtName = tdName.textContent || tdName.innerText;
          const txtClass = tdClass.textContent || tdClass.innerText;
          
          const matchText = txtId.toUpperCase().indexOf(input) > -1 || txtName.toUpperCase().indexOf(input) > -1;
          const matchClass = classVal === "" || txtClass.toUpperCase().indexOf(classVal) > -1;

          // Một hàng chỉ hiển thị khi thỏa cả điều kiện từ khóa và điều kiện lớp.
          tr[i].style.display = (matchText && matchClass) ? "" : "none";
        }
      }
    }
  