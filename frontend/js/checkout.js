/* ==========================================================
   checkout.js — หน้ากรอกข้อมูลผู้เข้าชม (/checkout)
   ========================================================== */

const summaryPanel = document.getElementById("summary-panel");
const checkoutForm = document.getElementById("checkout-form");
const errorBox = document.getElementById("error-box");
const submitBtn = document.getElementById("submit-btn");

const bookingId = getQueryParam("booking_id");
let selectedMethod = "promptpay";

document.querySelectorAll(".payment-option").forEach((el) => {
  el.addEventListener("click", () => {
    document.querySelectorAll(".payment-option").forEach((o) => o.classList.remove("selected"));
    el.classList.add("selected");
    selectedMethod = el.dataset.method;
  });
});

async function loadSummary() {
  if (!bookingId) {
    showError(summaryPanel, "ไม่พบข้อมูลการจอง กรุณาเริ่มใหม่จากหน้ารายการแข่งขัน");
    submitBtn.disabled = true;
    return;
  }
  try {
    const booking = await BookingAPI.get(bookingId);
    const race = await RaceAPI.getRace(booking.race_id);

    summaryPanel.innerHTML = `
      <div class="summary-box">
        <div class="row"><span>รายการแข่งขัน</span><span>${race.name}</span></div>
        <div class="row"><span>จำนวนตั๋ว</span><span>${booking.quantity} ใบ</span></div>
        <div class="total-row"><span>ยอดชำระ</span><span>${formatPrice(booking.total_price)}</span></div>
      </div>
    `;
  } catch (err) {
    showError(summaryPanel, err.message);
    submitBtn.disabled = true;
  }
}

checkoutForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorBox.innerHTML = "";

  const buyerName = document.getElementById("buyer-name").value.trim();
  const buyerPhone = document.getElementById("buyer-phone").value.trim();

  if (!/^0[0-9]{9}$/.test(buyerPhone)) {
    showError(errorBox, "กรุณากรอกเบอร์โทรศัพท์ให้ถูกต้อง (ขึ้นต้นด้วย 0 จำนวน 10 หลัก)");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "กำลังบันทึกข้อมูล...";

  try {
    await BookingAPI.submitCheckout(bookingId, buyerName, buyerPhone, selectedMethod);
    saveState({ bookingId: Number(bookingId) });
    window.location.href = `payment.html?booking_id=${bookingId}`;
  } catch (err) {
    showError(errorBox, err.message);
    submitBtn.disabled = false;
    submitBtn.textContent = "ไปหน้าชำระเงิน →";
  }
});

loadSummary();
