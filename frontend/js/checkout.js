/* ==========================================================
   checkout.js — หน้ากรอกข้อมูลผู้เข้าชม (/checkout)
   ========================================================== */

const summaryPanel = document.getElementById("summary-panel");
const checkoutForm = document.getElementById("checkout-form");
const errorBox = document.getElementById("error-box");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");
const countdownEl = document.getElementById("countdown");
const nameInput = document.getElementById("buyer-name");
const phoneInput = document.getElementById("buyer-phone");

const bookingId = getQueryParam("booking_id");

function disableForm(message) {
  submitBtn.disabled = true;
  cancelBtn.hidden = true;
  if (message) showError(errorBox, message);
}

function onExpired() {
  countdownEl.innerHTML = "⏱️ หมดเวลาล็อกที่นั่งแล้ว";
  countdownEl.classList.add("urgent");
  disableForm("หมดเวลาล็อกที่นั่งแล้ว ที่นั่งถูกคืนเข้าระบบ กรุณาเลือกโซนใหม่อีกครั้ง");
}

async function loadSummary() {
  if (!requireAuth()) {
    disableForm();
    return;
  }
  if (!bookingId) {
    showError(summaryPanel, "ไม่พบข้อมูลการจอง กรุณาเริ่มใหม่จากหน้ารายการแข่งขัน");
    disableForm();
    return;
  }
  try {
    const booking = await BookingAPI.get(bookingId);

    // สถานะเลยขั้นนี้ไปแล้ว -> พาไปหน้าที่ถูกต้อง
    if (["pending_review", "paid"].includes(booking.status)) {
      window.location.replace(`ticket-success.html?booking_id=${encodeURIComponent(bookingId)}`);
      return;
    }
    if (booking.status === "rejected") {
      window.location.replace(`payment.html?booking_id=${encodeURIComponent(bookingId)}`);
      return;
    }

    summaryPanel.innerHTML = `
      <div class="summary-box">
        <div class="row"><span>รายการแข่งขัน</span><span>${esc(booking.race_name)}</span></div>
        <div class="row"><span>วันแข่ง</span><span>${esc(booking.race_date)}</span></div>
        <div class="row"><span>โซน</span><span>${esc(booking.zone_name)} × ${booking.quantity} ใบ</span></div>
        <div class="total-row"><span>ยอดชำระ</span><span>${formatPrice(booking.total_price)}</span></div>
      </div>`;

    if (["expired", "cancelled"].includes(booking.status)) {
      disableForm(`การจองนี้${booking.status === "expired" ? "หมดเวลาแล้ว" : "ถูกยกเลิกแล้ว"} กรุณาเลือกโซนใหม่อีกครั้ง`);
      return;
    }

    if (booking.buyer_name) nameInput.value = booking.buyer_name;
    if (booking.buyer_phone) phoneInput.value = booking.buyer_phone;
    startCountdown(countdownEl, booking.seconds_left, onExpired);
  } catch (err) {
    showError(summaryPanel, err.message);
    disableForm();
  }
}

checkoutForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!requireAuth()) return;
  errorBox.innerHTML = "";

  const buyerName = nameInput.value.trim().replace(/\s+/g, " ");
  const buyerPhone = phoneInput.value.replace(/[\s-]/g, "");

  if (buyerName.length < 2) {
    showError(errorBox, "กรุณากรอกชื่อ-นามสกุลผู้ซื้อ");
    nameInput.focus();
    return;
  }
  if (!/^0[0-9]{9}$/.test(buyerPhone)) {
    showError(errorBox, "กรุณากรอกเบอร์โทรศัพท์ให้ถูกต้อง (ขึ้นต้นด้วย 0 จำนวน 10 หลัก)");
    phoneInput.focus();
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "กำลังบันทึกข้อมูล...";
  try {
    await BookingAPI.submitCheckout(bookingId, buyerName, buyerPhone);
    window.location.href = `payment.html?booking_id=${encodeURIComponent(bookingId)}`;
  } catch (err) {
    showError(errorBox, err.message);
    submitBtn.disabled = false;
    submitBtn.textContent = "ไปหน้าชำระเงิน →";
  }
});

cancelBtn.addEventListener("click", async () => {
  if (!confirm("ยืนยันยกเลิกการจองนี้? ที่นั่งจะถูกคืนเข้าระบบ")) return;
  try {
    await BookingAPI.cancel(bookingId);
    clearState();
    window.location.href = "my-tickets.html";
  } catch (err) {
    showError(errorBox, err.message);
  }
});

loadSummary();
