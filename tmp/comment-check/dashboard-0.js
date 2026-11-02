
    // Chỉ cập nhật đồng hồ; các số thống kê trên trang do Flask tính lúc tải HTML.
    function updateClock() {
      const d = new Date();
      document.getElementById('liveClock').innerText = d.toLocaleString('vi-VN');
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Hàm training riêng đã bị GỘP vào triggerFaceTraining() trong dashboard.js
    // (2 hàm này trước đây làm y hệt 1 việc ở 2 nơi khác nhau, dễ lệch khi sửa 1 nơi
    // mà quên nơi còn lại). Nút bấm phía trên giờ gọi thẳng hàm dùng chung đó.
  