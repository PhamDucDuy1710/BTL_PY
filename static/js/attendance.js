// Chuỗi JSON của lần tải trước để nhận biết nội dung lịch sử có thay đổi.
let lastLogSignature = null;
// Cờ chống chồng yêu cầu khi một lần gọi API mất hơn chu kỳ cập nhật một giây.
let polling = false;

// Cancel the MJPEG request when leaving, including entry into the back/forward cache.
// Khi rời trang, ngắt kết nối ảnh MJPEG để máy chủ biết người xem đã đóng.
window.addEventListener('pagehide', () => {
  const video = document.querySelector('.cam-box img');
  // Thay URL video bằng dữ liệu rỗng, không gọi endpoint dừng toàn bộ người xem khác.
  if (video) video.src = 'data:,';
});

window.addEventListener('pageshow', (event) => {
  // Trang khôi phục từ bộ nhớ Back/Forward cần mở lại URL video đã ngắt.
  if (event.persisted) {
    const video = document.querySelector('.cam-box img');
    if (video) video.src = '/video_feed';
  }
});

// Đồng hồ hiển thị thời gian thực phía trên
function initLiveDateTime() {
  const el = document.getElementById('screen-clock');
  const days = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
  
  function update() {
    const d = new Date();
    const time = d.toTimeString().split(' ')[0];
    el.innerText = `lúc ${time} ${days[d.getDay()]}, ${d.getDate()} tháng ${d.getMonth() + 1}, ${d.getFullYear()}`;
  }
  setInterval(update, 1000);
  update();
}

// Polling dữ liệu nhận diện & Bảng danh sách điểm danh
async function pollAttendanceState() {
  // Nếu lần tải trước chưa xong thì bỏ lượt này, tránh nhiều response về sai thứ tự.
  if (polling) return;
  polling = true;
  try {
    // 1. Quét thông tin sinh viên mới nhất
    const resCurrent = await fetch('/api/current-detected');
    if (!resCurrent.ok) throw new Error('Không tải được thông tin nhận diện');
    // API trả một đối tượng sinh viên hoặc null khi không còn nhận diện gần đây.
    const student = await resCurrent.json();
    const profileBox = document.getElementById('profile-box');

    if (student && student.student_id) {
      // escapeHtml() (định nghĩa trong dashboard.js, được nhúng trước file này) chống XSS
      profileBox.innerHTML = `
        <div class="student-card">
          <div class="student-head">
            <i class="fa-regular fa-id-card"></i>
            <span>${escapeHtml(student.student_id)}</span>
            <span style="opacity:0.3">•</span>
            <span>${escapeHtml(student.full_name)}</span>
          </div>
          <div class="student-meta">
            <span><i class="fa-solid fa-graduation-cap"></i> ${escapeHtml(student.class_id)}</span>
            <span class="cooldown-badge"><i class="fa-regular fa-clock"></i> ${escapeHtml(student.status)}</span>
            <span style="margin-left:auto;"><i class="fa-regular fa-calendar-check"></i> ${escapeHtml(student.time)}</span>
          </div>
        </div>
      `;
    }

    if (!student || !student.student_id) {
      profileBox.textContent = 'Đang đợi nhận diện khuôn mặt...';
    }

    // 2. Tải danh sách lịch sử ra vào
    const resLogs = await fetch('/api/access-logs');
    if (!resLogs.ok) throw new Error('Không tải được lịch sử');
    const logs = await resLogs.json();
    document.getElementById('total-logs-count').innerText = logs.length;

    // Chỉ vẽ lại bảng khi số lượng bản ghi có thay đổi
    // So toàn bộ nội dung bản ghi, không chỉ số lượng; sửa thông tin cũng khiến bảng cập nhật.
    const signature = JSON.stringify(logs);
    if (signature !== lastLogSignature) {
      lastLogSignature = signature;
      const tbody = document.getElementById('attendance-rows');
      tbody.innerHTML = logs.map(item => `
        <tr>
          <td style="font-weight:700; color: var(--slate-400);">${escapeHtml(item.stt)}</td>
          <td style="font-weight:700; color: var(--slate-900);">${escapeHtml(item.student_id)}</td>
          <td style="font-weight:600;">${escapeHtml(item.full_name)}</td>
          <td>${escapeHtml(item.class_name)}</td>
          <td><i class="fa-regular fa-clock" style="color: var(--blue-brand); margin-right:4px;"></i> ${escapeHtml(item.timestamp)}</td>
          <td>
            <img src="${escapeHtml(item.snapshot)}" class="snap-img" onerror="this.src='https://via.placeholder.com/44'" alt="Face">
          </td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error("Lỗi đồng bộ dữ liệu:", err);
  } finally {
    // Luôn trả cờ về trạng thái rảnh, kể cả khi tải API hoặc đọc JSON thất bại.
    polling = false;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initLiveDateTime();
  // Polling mỗi giây, độc lập với luồng video MJPEG trong thẻ img.
  setInterval(pollAttendanceState, 1000);
  // Tải ngay khi trang sẵn sàng, không chờ tới nhịp một giây đầu tiên.
  pollAttendanceState();
});

