/* ==========================================================
   ticket-success.js — หน้ารับ e-Ticket (/ticket-success)
   รอตรวจสลิป -> เช็กสถานะให้เองทุก 10 วินาที -> อนุมัติแล้วแสดง QR เข้างานทันที
   ========================================================== */

const ticketContent = document.getElementById("ticket-content");
const bookingId = getQueryParam("booking_id");
const POLL_MS = 10000;
let pollTimer = null;

function renderWaiting(b) {
  ticketContent.innerHTML = `
    <div class="state-card waiting">
      <div class="state-icon spin">⏳</div>
      <h1>ส่งสลิปเรียบร้อย รอตรวจสอบ</h1>
      <p>ทีมงานกำลังตรวจสอบการชำระเงิน เมื่ออนุมัติแล้ว e-Ticket จะแสดงที่หน้านี้ทันที<br />
         ปิดหน้านี้ได้ แล้วกลับมาดูที่เมนู <a href="my-tickets.html">“ตั๋วของฉัน”</a></p>
      <div class="summary-box">
        <div class="row"><span>รหัสการจอง</span><span>#${esc(b.id)}</span></div>
        <div class="row"><span>รายการ</span><span>${esc(b.race_name)} (${esc(b.race_date)})</span></div>
        <div class="row"><span>โซน</span><span>${esc(b.zone_name)} × ${b.quantity} ใบ</span></div>
        <div class="total-row"><span>ยอดชำระ</span><span>${formatPrice(b.total_price)}</span></div>
      </div>
      <p class="muted small">ตรวจสอบสถานะอัตโนมัติทุก 10 วินาที</p>
    </div>`;
}

function renderRejected(b) {
  ticketContent.innerHTML = `
    <div class="state-card rejected">
      <div class="state-icon">❌</div>
      <h1>สลิปไม่ผ่านการตรวจสอบ</h1>
      <p>เหตุผล: <strong>${esc(b.reject_reason || "-")}</strong></p>
      <p>กรุณาแนบสลิปใหม่ภายในเวลาที่กำหนด มิฉะนั้นที่นั่งจะถูกคืนเข้าระบบ</p>
      <a class="btn btn-primary btn-block" href="payment.html?booking_id=${encodeURIComponent(b.id)}">แนบสลิปใหม่ →</a>
    </div>`;
}

function renderClosed(b) {
  const text = {
    expired: "การจองนี้หมดเวลาแล้ว ที่นั่งถูกคืนเข้าระบบ",
    cancelled: b.reject_reason ? `การจองนี้ถูกยกเลิก (${b.reject_reason})` : "การจองนี้ถูกยกเลิกแล้ว",
  }[b.status] || b.status_label;
  ticketContent.innerHTML = `
    <div class="state-card closed">
      <div class="state-icon">🚫</div>
      <h1>${esc(text)}</h1>
      <p>หากโอนเงินไปแล้ว กรุณาติดต่อผู้จัดงานพร้อมสลิปและรหัสการจอง #${esc(b.id)}</p>
      <a class="btn btn-primary btn-block" href="races.html">ดูรายการแข่งขัน</a>
    </div>`;
}

function renderTicket(ticket) {
  ticketContent.innerHTML = `
    <div class="ticket-card">
      <div class="ticket-header">
        <div class="success-icon">✅</div>
        <h1 style="margin:0; font-size:1.4rem;">ชำระเงินสำเร็จ — นี่คือ e-Ticket ของคุณ</h1>
        <p style="margin:4px 0 0; opacity:0.9;">แสดง QR นี้ที่ประตูทางเข้าในวันงาน</p>
      </div>
      <div class="ticket-body">
        <div class="qr-box">
          <div class="qr-svg ticket-qr">${qrSvg(ticket.qr_code_data, { cellSize: 6 })}</div>
          <p class="ticket-code">${esc(ticket.ticket_code)}</p>
          ${ticket.checked_in_at ? `<p class="alert alert-warning">ใช้เข้างานแล้วเมื่อ ${esc(ticket.checked_in_at)}</p>` : ""}
        </div>
        <div class="info-row"><span class="label">รายการแข่งขัน</span><span>${esc(ticket.race_name)}</span></div>
        <div class="info-row"><span class="label">วันที่จัดงาน</span><span>${esc(ticket.race_date)}</span></div>
        <div class="info-row"><span class="label">สถานที่</span><span>${esc(ticket.venue)}</span></div>
        <div class="info-row"><span class="label">โซน</span><span>${esc(ticket.zone_name)}</span></div>
        <div class="info-row"><span class="label">จำนวน</span><span>${esc(ticket.quantity)} คน (QR เดียวเข้าได้ทั้งกลุ่ม)</span></div>
        <div class="info-row"><span class="label">ผู้เข้าชม</span><span>${esc(ticket.buyer_name)}</span></div>
      </div>
    </div>

    <div class="btn-row">
      <button class="btn btn-outline btn-block" id="save-btn">📥 บันทึกภาพ QR</button>
      <a href="my-tickets.html" class="btn btn-primary btn-block">ตั๋วของฉันทั้งหมด</a>
    </div>
    <p class="muted small center">อย่าแชร์ QR นี้ให้ผู้อื่น QR ใช้เข้างานได้ครั้งเดียว</p>`;

  document.getElementById("save-btn").addEventListener("click", () =>
    downloadQrPng(ticket.qr_code_data, `gridpass-${ticket.ticket_code}.png`, [
      ticket.ticket_code,
      `${ticket.race_name} • ${ticket.race_date}`,
      `${ticket.zone_name} × ${ticket.quantity} • ${ticket.buyer_name}`,
    ])
  );
}

async function load() {
  if (!requireAuth()) return;
  if (!bookingId) {
    showError(ticketContent, "ไม่พบข้อมูลตั๋ว กรุณาเปิดจากเมนู “ตั๋วของฉัน”");
    return;
  }
  try {
    const b = await BookingAPI.get(bookingId);
    clearTimeout(pollTimer);
    if (b.status === "paid") {
      renderTicket(await BookingAPI.getTicket(bookingId));
    } else if (b.status === "pending_review") {
      renderWaiting(b);
      pollTimer = setTimeout(load, POLL_MS);
    } else if (b.status === "rejected") {
      renderRejected(b);
    } else if (["pending", "awaiting_payment"].includes(b.status)) {
      window.location.replace(`payment.html?booking_id=${encodeURIComponent(bookingId)}`);
    } else {
      renderClosed(b);
    }
  } catch (err) {
    showError(ticketContent, err.message);
  }
}

load();
