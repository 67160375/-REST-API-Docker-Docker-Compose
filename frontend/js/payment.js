/* ==========================================================
   payment.js — หน้าชำระเงิน (/payment)
   หมายเหตุ: การชำระเงินในรอบนี้เป็น mock เท่านั้น ยังไม่ได้เชื่อม
   ผู้ให้บริการชำระเงินจริง (เตรียมไว้ในสัปดาห์ถัดไป)
   ========================================================== */

const paymentContent = document.getElementById("payment-content");
const confirmBtn = document.getElementById("confirm-payment-btn");
const errorBox = document.getElementById("error-box");

const bookingId = getQueryParam("booking_id");
let currentBooking = null;

function fakeQrSvg() {
  // สุ่มลาย QR ปลอมๆ ด้วยตาราง 8x8 (เพื่อความสวยงามเท่านั้น ไม่ใช่ QR จริง)
  let cells = "";
  for (let y = 0; y < 8; y++) {
    for (let x = 0; x < 8; x++) {
      if (Math.random() > 0.5) {
        cells += `<rect x="${x * 20}" y="${y * 20}" width="18" height="18" fill="#1c1c1c" />`;
      }
    }
  }
  return `<svg width="160" height="160" viewBox="0 0 160 160">${cells}</svg>`;
}

function renderPayment(booking) {
  paymentContent.innerHTML = `
    <div class="summary-box">
      <div class="row"><span>รหัสการจอง</span><span>#${booking.id}</span></div>
      <div class="total-row"><span>ยอดที่ต้องชำระ</span><span>${formatPrice(booking.total_price)}</span></div>
    </div>

    <div class="qr-box">
      ${fakeQrSvg()}
      <p style="margin:0; font-weight:700;">สแกนเพื่อชำระผ่านพร้อมเพย์</p>
      <p style="margin:4px 0 0; color:#6b6b6b; font-size:0.85rem;">ยอดชำระ ${formatPrice(booking.total_price)}</p>
    </div>
  `;
}

confirmBtn.addEventListener("click", async () => {
  if (!currentBooking) return;
  confirmBtn.disabled = true;
  confirmBtn.textContent = "กำลังประมวลผลการชำระเงิน...";
  errorBox.innerHTML = "";

  try {
    await BookingAPI.pay(bookingId, currentBooking.payment_method || "promptpay");
    window.location.href = `ticket-success.html?booking_id=${bookingId}`;
  } catch (err) {
    showError(errorBox, err.message);
    confirmBtn.disabled = false;
    confirmBtn.textContent = "ยืนยันการชำระเงิน";
  }
});

async function loadBooking() {
  if (!bookingId) {
    showError(paymentContent, "ไม่พบข้อมูลการจอง กรุณาเริ่มใหม่จากหน้ารายการแข่งขัน");
    confirmBtn.disabled = true;
    return;
  }
  try {
    currentBooking = await BookingAPI.get(bookingId);
    renderPayment(currentBooking);
  } catch (err) {
    showError(paymentContent, err.message);
    confirmBtn.disabled = true;
  }
}

loadBooking();
