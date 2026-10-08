// Cập nhật đồng hồ Header
function startClock() {
  const clockEl = document.getElementById('top-clock-display');
  if (!clockEl) return;
  
  setInterval(() => {
    const d = new Date();
    clockEl.innerText = d.toLocaleString('vi-VN');
  }, 1000);
}

// HÀM DÙNG CHUNG TOÀN HỆ THỐNG: escape các ký tự HTML đặc biệt trước khi
// chèn dữ liệu (đến từ API, tức có thể là dữ liệu do người dùng nhập khi đăng ký
// sinh viên) vào innerHTML. Thiếu bước này, nếu ai đó đăng ký tên sinh viên chứa
// mã HTML/script (vd: "<script>alert(1)</script>"), trình duyệt sẽ THỰC THI đoạn
// mã đó khi render lại lên bảng điểm danh (lỗ hổng XSS - Cross-Site Scripting).
function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = (value === null || value === undefined) ? '' : String(value);
  return div.innerHTML;
}

// Kích hoạt API Training đặc trưng khuôn mặt
// (HÀM DÙNG CHUNG DUY NHẤT - trước đây có 2 bản gần giống hệt nhau ở dashboard.html
// và dashboard.js, nay gộp về đây để tránh 2 nơi lệch hành vi khi sửa)
async function triggerFaceTraining() {
  const btn = document.getElementById('btn-train-action');
  if (!confirm("Bắt đầu huấn luyện lại dữ liệu khuôn mặt?")) return;

  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang huấn luyện...`;

  try {
    const res = await fetch('/api/train', { method: 'POST' });
    const json = await res.json();
    if (res.ok) {
      alert("Thành công: " + (json.message || "Đã trích xuất xong!"));
      location.reload();
    } else {
      alert("Lỗi: " + (json.message || "Không thể huấn luyện"));
    }
  } catch (err) {
    alert("Lỗi kết nối tới máy chủ khi huấn luyện!");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  startClock();
});