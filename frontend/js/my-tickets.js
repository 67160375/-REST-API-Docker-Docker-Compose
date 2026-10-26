/* ==========================================================
   my-tickets.js — หน้าตั๋วของฉัน (/my-tickets)
   ========================================================== */

const listEl = document.getElementById("booking-list");
const errorBox = document.getElementById("error-box");

function actionFor(b) {
  const id = encodeURIComponent(b.id);
  switch (b.status) {
    case "paid":
      return `<a class="btn btn-primary btn-sm" href="ticket-success.html?booking_id=${id}">ดู e-Ticket / QR</a>`;
    case "pending":
      return `<a class="btn btn-primary btn-sm" href="checkout.html?booking_id=${id}">กรอกข้อมูลต่อ</a>`;
    case "awaiting_payment":
      return `<a class="btn btn-primary btn-sm" href="payment.html?booking_id=${id}">ชำระเงิน / แนบสลิป</a>`;
    case "rejected":
      return `<a class="btn btn-primary btn-sm" href="payment.html?booking_id=${id}">แนบสลิปใหม่</a>`;
    case "pending_review":
      return `<a class="btn btn-outline btn-sm" href="ticket-success.html?booking_id=${id}">ดูสถานะ</a>`;
    default:
      return "";
  }
}

function canCancel(b) {
  return ["pending", "awaiting_payment", "rejected"].includes(b.status);
}

function render(bookings) {
  if (!bookings.length) {
    listEl.innerHTML = `
      <div class="empty-state">
        ยังไม่มีการจอง<br /><br />
        <a class="btn btn-primary" href="races.html">ดูรายการแข่งขัน</a>
      </div>`;
    return;
  }
  listEl.innerHTML = bookings
    .map(
      (b) => `
      <article class="booking-card status-${esc(b.status)}">
        <div class="booking-main">
          <div class="booking-top">
            ${statusBadge(b.status, b.status_label)}
            <span class="muted small">#${esc(b.id)}</span>
          </div>
          <h3>${esc(b.race_name)}</h3>
          <div class="meta">📅 ${esc(b.race_date)} • ${esc(b.zone_name)} × ${b.quantity} ใบ • ${formatPrice(b.total_price)}</div>
          ${b.status === "rejected" && b.reject_reason ? `<div class="meta danger">เหตุผล: ${esc(b.reject_reason)}</div>` : ""}
          ${b.seconds_left != null && b.seconds_left > 0 ? `<div class="meta warn">⏱️ เหลือเวลาอีก ${formatCountdown(b.seconds_left)} นาที</div>` : ""}
        </div>
        <div class="booking-actions">
          ${actionFor(b)}
          ${canCancel(b) ? `<button type="button" class="btn btn-link btn-sm" data-cancel="${esc(b.id)}">ยกเลิก</button>` : ""}
        </div>
      </article>`
    )
    .join("");

  listEl.querySelectorAll("[data-cancel]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      if (!confirm(`ยืนยันยกเลิกการจอง #${btn.dataset.cancel}? ที่นั่งจะถูกคืนเข้าระบบ`)) return;
      btn.disabled = true;
      try {
        await BookingAPI.cancel(btn.dataset.cancel);
        load();
      } catch (err) {
        showError(errorBox, err.message);
        btn.disabled = false;
      }
    })
  );
}

async function load() {
  if (!requireAuth()) {
    listEl.innerHTML = "";
    return;
  }
  try {
    render(await BookingAPI.mine());
  } catch (err) {
    showError(listEl, err.message);
  }
}

load();
