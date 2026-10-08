let lastRecordCount = -1;

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
  try {
    // 1. Quét thông tin sinh viên mới nhất
    const resCurrent = await fetch('/api/current-detected');
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

    // 2. Tải danh sách lịch sử ra vào
    const resLogs = await fetch('/api/access-logs');
    const logs = await resLogs.json();
    document.getElementById('total-logs-count').innerText = logs.length;

    // Chỉ vẽ lại bảng khi số lượng bản ghi có thay đổi
    if (logs.length !== lastRecordCount) {
      lastRecordCount = logs.length;
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
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initLiveDateTime();
  setInterval(pollAttendanceState, 1000);
  pollAttendanceState();
});