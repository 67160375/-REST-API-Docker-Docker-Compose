/* ==========================================================
   ticket-success.js — หน้ารับ e-Ticket (/ticket-success)
   ========================================================== */

const ticketContent = document.getElementById("ticket-content");
const bookingId = getQueryParam("booking_id");

function fakeQrSvg() {
  let cells = "";
  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 8; x++) {
      if (Math.random() > 0.5) {
        cells += `<rect x="${x * 20}" y="${y * 20}" width="18" height="18" fill="#1c1c1c" />`;
      }
    }
  }
  return `<svg width="140" height="140" viewBox="0 0 140 140">${cells}</svg>`;
}

function renderTicket(ticket) {
  ticketContent.innerHTML = `
    <div class="ticket-card">
      <div class="ticket-header">
        <div class="success-icon">✅</div>
        <h1 style="margin:0; font-size:1.4rem;">จองตั๋วสำเร็จ!</h1>
        <p style="margin:4px 0 0; opacity:0.9;">e-Ticket ของคุณพร้อมใช้งานแล้ว</p>
      </div>
      <div class="ticket-body">
        <div class="qr-box">
          ${fakeQrSvg()}
          <p class="ticket-code">${ticket.ticket_code}</p>
        </div>

        <div class="info-row"><span class="label">รายการแข่งขัน</span><span>${ticket.race_name}</span></div>
        <div class="info-row"><span class="label">โซน</span><span>${ticket.zone_name}</span></div>
        <div class="info-row"><span class="label">จำนวนตั๋ว</span><span>${ticket.quantity} ใบ</span></div>
        <div class="info-row"><span class="label">ผู้เข้าชม</span><span>${ticket.buyer_name}</span></div>
        <div class="info-row"><span class="label">วันที่จัดงาน</span><span>${ticket.race_date}</span></div>
        <div class="info-row"><span class="label">สถานที่</span><span>${ticket.venue}</span></div>
      </div>
    </div>

    <div style="display:flex; gap:12px;">
      <button class="btn btn-outline btn-block" id="save-btn">📥 ดาวน์โหลด/เซฟภาพ</button>
      <a href="races.html" class="btn btn-primary btn-block">ดูรายการแข่งขันอื่น</a>
    </div>
  `;

  document.getElementById("save-btn").addEventListener("click", () => {
    alert("บันทึกรูป QR Code e-Ticket ลงในโทรศัพท์เรียบร้อย (ฟังก์ชันเดโม)");
    clearState();
  });
}

async function loadTicket() {
  if (!bookingId) {
    showError(ticketContent, "ไม่พบข้อมูลตั๋ว กรุณาเริ่มใหม่จากหน้ารายการแข่งขัน");
    return;
  }
  try {
    const ticket = await BookingAPI.getTicket(bookingId);
    renderTicket(ticket);
  } catch (err) {
    showError(ticketContent, err.message);
  }
}

loadTicket();
