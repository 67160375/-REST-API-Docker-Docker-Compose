/* ==========================================================
   payment.js — หน้าชำระเงิน (/payment)
   QR พร้อมเพย์ฝังยอดเงินมาจาก backend -> ลูกค้าโอน -> แนบสลิป -> รอแอดมินตรวจ
   ========================================================== */

const paymentContent = document.getElementById("payment-content");
const countdownEl = document.getElementById("countdown");
const slipForm = document.getElementById("slip-form");
const slipInput = document.getElementById("slip-input");
const slipPreview = document.getElementById("slip-preview");
const slipPlaceholder = document.getElementById("slip-placeholder");
const submitBtn = document.getElementById("submit-slip-btn");
const errorBox = document.getElementById("error-box");

const bookingId = getQueryParam("booking_id");
const MAX_BYTES = 5 * 1024 * 1024;
let selectedFile = null;

function goTicket() {
  window.location.replace(`ticket-success.html?booking_id=${encodeURIComponent(bookingId)}`);
}

function onExpired() {
  countdownEl.innerHTML = "⏱️ หมดเวลาชำระเงินแล้ว";
  countdownEl.classList.add("urgent");
  slipForm.hidden = true;
  showError(paymentContent, "หมดเวลาชำระเงินแล้ว ที่นั่งถูกคืนเข้าระบบ หากโอนเงินไปแล้ว กรุณาติดต่อผู้จัดงานพร้อมสลิป");
}

function renderPayment(info) {
  const b = info.booking;
  const rejected = b.status === "rejected"
    ? `<div class="alert alert-error">❌ สลิปก่อนหน้าไม่ผ่านการตรวจสอบ: <strong>${esc(b.reject_reason || "-")}</strong><br />กรุณาแนบสลิปใหม่ภายในเวลาที่เหลือ</div>`
    : "";

  const qrBlock = info.promptpay_payload
    ? `
      <div class="qr-box promptpay-box">
        <div class="pp-header">PromptPay</div>
        <div class="qr-svg">${qrSvg(info.promptpay_payload, { cellSize: 6 })}</div>
        <div class="pp-amount">${formatPrice(info.amount)}</div>
        ${info.promptpay_name ? `<div class="pp-name">ชื่อบัญชี: <strong>${esc(info.promptpay_name)}</strong></div>` : ""}
        <div class="pp-id muted small">พร้อมเพย์: ${esc(info.promptpay_masked_id || "")}</div>
        <button type="button" class="btn btn-outline btn-sm" id="save-qr-btn">📥 บันทึกรูป QR (สำหรับเปิดในแอปธนาคาร)</button>
      </div>
      <ol class="how-to">
        <li>เปิดแอปธนาคาร เลือก “สแกนจ่าย” แล้วสแกน QR นี้ (ถ้าใช้มือถือเครื่องเดียวกัน กดบันทึกรูป QR แล้วเลือกรูปจากแกลเลอรี)</li>
        <li>ตรวจว่ายอดเงิน <strong>${formatPrice(info.amount)}</strong> และชื่อบัญชีถูกต้อง แล้วยืนยันการโอน</li>
        <li>แนบรูปสลิปด้านล่าง แล้วกดส่ง</li>
      </ol>`
    : `<div class="alert alert-error">⚠️ ${esc(info.config_error || "ยังชำระเงินไม่ได้ในขณะนี้")}</div>`;

  paymentContent.innerHTML = `
    ${rejected}
    <div class="summary-box">
      <div class="row"><span>รหัสการจอง</span><span>#${esc(b.id)}</span></div>
      <div class="row"><span>รายการ</span><span>${esc(b.race_name)}</span></div>
      <div class="row"><span>โซน</span><span>${esc(b.zone_name)} × ${b.quantity} ใบ</span></div>
      <div class="total-row"><span>ยอดที่ต้องชำระ</span><span>${formatPrice(info.amount)}</span></div>
    </div>
    ${qrBlock}`;

  const saveBtn = document.getElementById("save-qr-btn");
  if (saveBtn) {
    saveBtn.addEventListener("click", () =>
      downloadQrPng(info.promptpay_payload, `gridpass-promptpay-${b.id}.png`, [
        `PromptPay ${Number(info.amount).toLocaleString("th-TH")} บาท`,
        `Grid Pass การจอง #${b.id}`,
      ])
    );
  }
  slipForm.hidden = !info.promptpay_payload;
}

slipInput.addEventListener("change", () => {
  errorBox.innerHTML = "";
  const file = slipInput.files[0];
  selectedFile = null;
  submitBtn.disabled = true;
  if (!file) return;
  if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
    showError(errorBox, "รองรับเฉพาะรูปภาพ JPG, PNG หรือ WEBP");
    return;
  }
  if (file.size > MAX_BYTES) {
    showError(errorBox, "ไฟล์ใหญ่เกิน 5MB กรุณาเลือกรูปที่เล็กลง");
    return;
  }
  selectedFile = file;
  slipPreview.src = URL.createObjectURL(file);
  slipPreview.hidden = false;
  slipPlaceholder.hidden = true;
  submitBtn.disabled = false;
});

slipForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedFile || !requireAuth()) return;
  submitBtn.disabled = true;
  submitBtn.textContent = "กำลังส่งสลิป...";
  errorBox.innerHTML = "";
  try {
    await BookingAPI.uploadSlip(bookingId, selectedFile);
    clearState();
    goTicket();
  } catch (err) {
    showError(errorBox, err.message);
    submitBtn.disabled = false;
    submitBtn.textContent = "ส่งสลิปเพื่อยืนยันการชำระเงิน";
    if (err.status === 410) onExpired();
  }
});

async function loadPayment() {
  if (!requireAuth()) return;
  if (!bookingId) {
    showError(paymentContent, "ไม่พบข้อมูลการจอง กรุณาเริ่มใหม่จากหน้ารายการแข่งขัน");
    return;
  }
  try {
    const info = await BookingAPI.paymentInfo(bookingId);
    const status = info.booking.status;
    if (["pending_review", "paid"].includes(status)) return goTicket();
    if (status === "pending") {
      window.location.replace(`checkout.html?booking_id=${encodeURIComponent(bookingId)}`);
      return;
    }
    if (["expired", "cancelled"].includes(status)) {
      showError(paymentContent, `การจองนี้${status === "expired" ? "หมดเวลาแล้ว" : "ถูกยกเลิกแล้ว"} กรุณาจองใหม่อีกครั้ง`);
      return;
    }
    renderPayment(info);
    startCountdown(countdownEl, info.booking.seconds_left, onExpired);
  } catch (err) {
    showError(paymentContent, err.message);
  }
}

loadPayment();
