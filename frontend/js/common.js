/* ==========================================================
   common.js — ฟังก์ชันช่วยเหลือและคลังคำแปลรวมทุกหน้า (Master i18n)
   ========================================================== */

const STORAGE_KEY = "Grid_Pass_state";

/* ==========================================================
   🌐 ระบบสลับภาษา (i18n) & คลังคำแปลครอบคลุมทุกหน้าในระบบ
   ========================================================== */
const translations = {
  th: {
    // Header & Navigation & Footer
    races: "รายการแข่งขัน",
    schedule: "ตารางการแข่ง",
    my_tickets: "ตั๋วของฉัน",
    admin: "แอดมิน",
    scan: "สแกนตั๋ว",
    login_btn: "เข้าสู่ระบบ / สมัครสมาชิก",
    welcome: "ยินดีต้อนรับ",
    account: "จัดการบัญชี",
    logout: "ออกจากระบบ",
    currency: "บาท",
    footer: "Grid Pass — ระบบจองตั๋วชมการแข่งขันรถ (เดโม)",
    
    // Auth Modal & Pages
    auth_title: "กรุณาเข้าสู่ระบบ",
    auth_desc: "คุณต้องเข้าสู่ระบบสมาชิก Grid Pass ก่อนดำเนินการจองตั๋ว",
    cancel: "ยกเลิก",
    go_to_login: "ไปหน้าเข้าสู่ระบบ",
    login_tab: "เข้าสู่ระบบ",
    register_tab: "สมัครสมาชิก",
    username: "ชื่อผู้ใช้งาน",
    password: "รหัสผ่าน",
    confirm_password: "ยืนยันรหัสผ่าน",
    email: "อีเมล",
    login_submit: "เข้าสู่ระบบ",
    register_submit: "ลงทะเบียนสมาชิก",

    // Stepper (ขั้นตอนบนหน้าเว็บ 1-6)
    step1: "1. ค้นหารายการแข่ง",
    step2: "2. ดูรายละเอียด",
    step3: "3. เลือกโซน",
    step4: "4. กรอกข้อมูล",
    step5: "5. ชำระเงิน",
    step6: "6. รับ e-Ticket",

    // หน้า 1: ค้นหารายการแข่ง (Races Page)
    search_title: "ค้นหารายการแข่งขัน",
    search_sub: "เลือกดูรายการแข่งรถที่สนใจ วันที่จัด สถานที่สนาม และราคาเริ่มต้น",
    search_placeholder: "ค้นหา เช่น Thailand Super Series, มอเตอร์ไซค์...",
    search_btn: "ค้นหา",
    from_price: "เริ่มต้น",
    no_races_found: "ไม่พบรายการแข่งขันที่ตรงกับคำค้นหา",
    loading_races: "กำลังโหลดรายการแข่งขัน...",

    // หน้า 2: รายละเอียดรายการแข่ง (Race Detail Page)
    schedule_title: "ตารางเวลา",
    race_date: "วันที่จัดงาน",
    venue: "สถานที่",
    activities: "กิจกรรมในงาน",
    venue_map: "ผังสนาม (Venue Map)",
    select_zone_btn: "เลือกโซนที่นั่ง →",
    no_activities: "ไม่มีข้อมูลกิจกรรม",
    err_no_race_id: "ไม่พบรหัสรายการแข่งขัน กรุณากลับไปเลือกใหม่",

    // หน้า 3: เลือกโซน (Select Zone Page)
    select_zone_title: "เลือกโซนและจำนวนตั๋ว",
    select_zone_sub: "เลือกโซนที่ต้องการนั่งชมและระบุจำนวนตั๋วที่ต้องการ",
    available_seats: "เหลือ {n} ที่นั่ง",
    sold_out: "ตั๋วหมดแล้ว",
    summary_title: "สรุปรายการสั่งซื้อ",
    summary_zone: "โซน:",
    summary_price: "ราคาต่อใบ:",
    summary_total: "ราคารวม:",
    confirm_zone_btn: "ล็อกที่นั่งชั่วคราว →",
    locking_seats: "กำลังล็อกที่นั่ง...",

    // หน้า 4: กรอกข้อมูลผู้จอง (Passenger Info Page)
    info_title: "กรอกข้อมูลผู้จองตั๋ว",
    info_sub: "โปรดกรอกข้อมูลให้ครบถ้วนเพื่อใช้ออก e-Ticket",
    fname: "ชื่อจริง",
    lname: "นามสกุล",
    phone: "เบอร์โทรศัพท์",
    id_card: "เลขบัตรประชาชน / พาสปอร์ต",
    proceed_to_payment: "ไปหน้าชำระเงิน →",
    fill_required: "กรุณากรอกข้อมูลให้ครบถ้วนทุกช่อง",

    // หน้า 5: ชำระเงิน (Payment Page)
    payment_title: "ชำระเงิน",
    payment_sub: "สแกน QR Code หรือชำระผ่านบัตรเครดิตเพื่อยืนยันคำสั่งซื้อ",
    pay_promptpay: "ชำระผ่าน PromptPay QR Code",
    pay_card: "ชำระผ่านบัตรเครดิต / เดบิต",
    upload_slip: "แนบสลิปการโอนเงิน",
    confirm_payment_btn: "ยืนยันการชำระเงิน",
    payment_processing: "กำลังตรวจสอบการชำระเงิน...",

    // หน้า 6: รับ e-Ticket (e-Ticket Page)
    ticket_title: "จองตั๋วสำเร็จ!",
    ticket_sub: "ขอบคุณที่ใช้บริการ Grid Pass แสดง QR Code นี้เพื่อเข้างาน",
    booking_ref: "รหัสการจอง:",
    download_pdf: "ดาวน์โหลด e-Ticket (PDF)",
    back_to_home: "กลับหน้าหลัก"
  },
  en: {
    // Header & Navigation & Footer
    races: "Races",
    schedule: "Schedule",
    my_tickets: "My Tickets",
    admin: "Admin",
    scan: "Scan Tickets",
    login_btn: "Login / Register",
    welcome: "Welcome",
    account: "Account",
    logout: "Logout",
    currency: "THB",
    footer: "Grid Pass — Motorsports Ticket Booking Demo System",
    
    // Auth Modal & Pages
    auth_title: "Authentication Required",
    auth_desc: "You must log in to your Grid Pass account before booking tickets.",
    cancel: "Cancel",
    go_to_login: "Go to Login",
    login_tab: "Login",
    register_tab: "Register",
    username: "Username",
    password: "Password",
    confirm_password: "Confirm Password",
    email: "Email Address",
    login_submit: "Sign In",
    register_submit: "Create Account",

    // Stepper
    step1: "1. Search Races",
    step2: "2. View Details",
    step3: "3. Select Zone",
    step4: "4. Fill Info",
    step5: "5. Payment",
    step6: "6. Get e-Ticket",

    // Page 1: Races Page
    search_title: "Search Races",
    search_sub: "Explore racing events, dates, circuits, and starting prices.",
    search_placeholder: "Search e.g. Thailand Super Series, Superbike...",
    search_btn: "Search",
    from_price: "From",
    no_races_found: "No races found matching your search.",
    loading_races: "Loading races...",

    // Page 2: Race Detail Page
    schedule_title: "Schedule",
    race_date: "Event Date",
    venue: "Venue",
    activities: "Event Activities",
    venue_map: "Venue Map",
    select_zone_btn: "Select Seating Zone →",
    no_activities: "No activity details available",
    err_no_race_id: "Race ID not found. Please select again.",

    // Page 3: Select Zone Page
    select_zone_title: "Select Zone & Ticket Quantity",
    select_zone_sub: "Choose your preferred seating zone and ticket quantity.",
    available_seats: "{n} seats left",
    sold_out: "Sold Out",
    summary_title: "Booking Summary",
    summary_zone: "Zone:",
    summary_price: "Price per ticket:",
    summary_total: "Total Price:",
    confirm_zone_btn: "Reserve Seats →",
    locking_seats: "Reserving seats...",

    // Page 4: Passenger Info Page
    info_title: "Passenger Information",
    info_sub: "Please enter correct information for your e-Ticket.",
    fname: "First Name",
    lname: "Last Name",
    phone: "Phone Number",
    id_card: "ID Card / Passport No.",
    proceed_to_payment: "Proceed to Payment →",
    fill_required: "Please fill in all required fields.",

    // Page 5: Payment Page
    payment_title: "Payment",
    payment_sub: "Scan QR Code or pay via Credit Card to complete your booking.",
    pay_promptpay: "Pay via PromptPay QR Code",
    pay_card: "Pay via Credit / Debit Card",
    upload_slip: "Upload Transfer Slip",
    confirm_payment_btn: "Confirm Payment",
    payment_processing: "Processing payment...",

    // Page 6: e-Ticket Page
    ticket_title: "Booking Confirmed!",
    ticket_sub: "Thank you for choosing Grid Pass. Show this QR Code at venue entrance.",
    booking_ref: "Booking Ref:",
    download_pdf: "Download e-Ticket (PDF)",
    back_to_home: "Back to Home"
  }
};

function getCurrentLang() {
  return localStorage.getItem("app_lang") || "th";
}

function t(key, params = {}) {
  const lang = getCurrentLang();
  let text = translations[lang]?.[key] || key;
  Object.keys(params).forEach((pKey) => {
    text = text.replace(`{${pKey}}`, params[pKey]);
  });
  return text;
}

window.toggleLanguage = function () {
  const current = getCurrentLang();
  localStorage.setItem("app_lang", current === "th" ? "en" : "th");
  window.location.reload();
};

/* ==========================================================
   🛡️ กันการแทรก HTML/สคริปต์ (XSS)
   ข้อมูลทุกอย่างที่มาจากผู้ใช้หรือ API ต้องผ่าน esc() ก่อนใส่ลง innerHTML
   ========================================================== */
function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/* ==========================================================
   🌐 ฟังก์ชันกวาดแปลภาษาอัตโนมัติทั้ง DOM (รองรับ text, placeholder, value)
   ========================================================== */
function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.getAttribute("data-i18n-placeholder"));
  });
  document.querySelectorAll("[data-i18n-value]").forEach((el) => {
    el.value = t(el.getAttribute("data-i18n-value"));
  });
}

/* ==========================================================
   ผู้ใช้ที่ล็อกอินอยู่
   ========================================================== */
function getToken() {
  const tk = localStorage.getItem("token");
  return tk && tk !== "null" && tk !== "undefined" && tk.trim() !== "" ? tk : null;
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("user")) || null;
  } catch (e) {
    return null;
  }
}

function currentPathWithQuery() {
  return window.location.pathname + window.location.search;
}

function loginUrl(next = currentPathWithQuery()) {
  return `/pages/auth.html?next=${encodeURIComponent(next)}`;
}

/* ==========================================================
   Header & Footer
   ========================================================== */
function renderHeader() {
  document.querySelector("header.site-header")?.remove();
  const header = document.createElement("header");
  header.className = "site-header";

  const user = getToken() ? getUser() : null;
  const path = window.location.pathname;
  const link = (href, label) =>
    `<a href="${href}" class="nav-link ${path === href ? "active" : ""}">${esc(label)}</a>`;

  let roleLinks = "";
  if (user && user.role === "admin") roleLinks += link("/pages/admin.html", t("admin"));
  if (user && (user.role === "admin" || user.role === "staff")) roleLinks += link("/pages/scan.html", t("scan"));

  const authHtml = user
    ? `<span class="nav-user">${esc(t("welcome"))}, <strong>${esc(user.username)}</strong></span>
       <a href="/pages/auth.html" class="nav-link">${esc(t("account"))}</a>
       <button type="button" class="nav-btn" onclick="handleMainLogout()">${esc(t("logout"))}</button>`
    : `<a href="${loginUrl()}" class="nav-btn nav-btn-primary">${esc(t("login_btn"))}</a>`;

  header.innerHTML = `
    <div class="header-inner">
      <a href="/pages/races.html" class="logo"><span class="flag">🏁</span> Grid Pass</a>
      <nav class="site-nav">
        ${link("/pages/races.html", t("races"))}
        ${link("/pages/schedule.html", t("schedule"))}
        ${user ? link("/pages/my-tickets.html", t("my_tickets")) : ""}
        ${roleLinks}
        ${authHtml}
        <button type="button" class="nav-btn" onclick="toggleLanguage()">🌐 ${getCurrentLang().toUpperCase()}</button>
      </nav>
    </div>
  `;
  document.body.prepend(header);
}

window.handleMainLogout = function () {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  window.location.href = "/pages/races.html";
};

function renderFooter() {
  const footer = document.createElement("footer");
  footer.className = "site-footer";
  footer.innerHTML = `&copy; 2026 ${esc(t("footer"))}`;
  document.body.appendChild(footer);
}

// ดึงสิทธิ์ล่าสุดจาก server (เช่น เพิ่งถูกตั้งเป็น admin) แล้ววาด header ใหม่ถ้าเปลี่ยน
async function refreshCurrentUser() {
  if (!getToken() || typeof UserAPI === "undefined") return;
  try {
    const me = await UserAPI.me();
    const old = getUser() || {};
    localStorage.setItem("user", JSON.stringify(me));
    if (old.role !== me.role || old.username !== me.username) renderHeader();
  } catch (e) {
    if (e.status === 401) renderHeader(); // token หมดอายุ (api.js ล้างให้แล้ว)
  }
}

/* ==========================================================
   State & Utility Functions
   ========================================================== */
function saveState(partial) {
  const next = { ...getState(), ...partial };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  return next;
}

function getState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch (e) {
    return {};
  }
}

function clearState() {
  localStorage.removeItem(STORAGE_KEY);
}

function formatPrice(number) {
  const lang = getCurrentLang();
  const formattedNum = Number(number).toLocaleString(lang === "th" ? "th-TH" : "en-US");
  return `${formattedNum} ${t("currency")}`;
}

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function showError(container, message) {
  if (container) {
    container.innerHTML = `<div class="alert alert-error">⚠️ ${esc(message)}</div>`;
  }
}

function showNotice(container, message, kind = "warning") {
  if (container) {
    container.innerHTML = `<div class="alert alert-${kind}">${esc(message)}</div>`;
  }
}

// ป้ายสถานะการจอง (สีตามสถานะ)
function statusBadge(status, label) {
  return `<span class="status-badge status-${esc(status)}">${esc(label || status)}</span>`;
}

/* ==========================================================
   ⏱️ นับเวลาถอยหลัง (ใช้ seconds_left ที่ server คำนวณมาให้ ไม่พึ่งนาฬิกาเครื่องลูกค้า)
   ========================================================== */
function formatCountdown(totalSeconds) {
  const s = Math.max(0, Math.floor(totalSeconds));
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

function startCountdown(el, seconds, onExpire) {
  if (!el || seconds == null) return null;
  const endAt = Date.now() + seconds * 1000;
  const tick = () => {
    const left = Math.round((endAt - Date.now()) / 1000);
    el.innerHTML = `⏱️ เหลือเวลา <strong>${formatCountdown(left)}</strong> นาที`;
    el.classList.toggle("urgent", left <= 60);
    if (left <= 0) {
      clearInterval(timer);
      if (onExpire) onExpire();
    }
  };
  const timer = setInterval(tick, 1000);
  tick();
  return timer;
}

/* ==========================================================
   🔳 QR Code (ใช้ไลบรารี vendor/qrcode-generator.js)
   ========================================================== */
function qrSvg(text, { cellSize = 5, margin = 2 } = {}) {
  if (typeof qrcode !== "function") return `<div class="alert alert-error">โหลดตัวสร้าง QR ไม่สำเร็จ</div>`;
  const qr = qrcode(0, "M");
  qr.addData(text);
  qr.make();
  return qr.createSvgTag({ cellSize, margin, scalable: true });
}

// บันทึก QR เป็นไฟล์ PNG พร้อมข้อความใต้ภาพ (ลูกค้าเปิดจากแกลเลอรีในแอปธนาคารได้)
function downloadQrPng(text, filename, captionLines = []) {
  const qr = qrcode(0, "M");
  qr.addData(text);
  qr.make();
  const count = qr.getModuleCount();
  const cell = 10, margin = 4 * cell, qrSize = count * cell;
  const lineH = 34;
  const canvas = document.createElement("canvas");
  canvas.width = qrSize + margin * 2;
  canvas.height = qrSize + margin * 2 + captionLines.length * lineH + (captionLines.length ? 16 : 0);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#1c1c1c";
  for (let r = 0; r < count; r++) {
    for (let c = 0; c < count; c++) {
      if (qr.isDark(r, c)) ctx.fillRect(margin + c * cell, margin + r * cell, cell, cell);
    }
  }
  ctx.textAlign = "center";
  captionLines.forEach((line, i) => {
    ctx.font = `${i === 0 ? "bold " : ""}26px 'Noto Sans Thai', sans-serif`;
    ctx.fillText(line, canvas.width / 2, qrSize + margin * 2 + i * lineH + 10);
  });
  canvas.toBlob((blob) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      URL.revokeObjectURL(a.href);
      a.remove();
    }, 1000);
  }, "image/png");
}

/* ==========================================================
   🔒 Authentication Check (Modal เตือนธีมสีแดง Grid Pass)
   ========================================================== */
function requireAuth(redirectUrl = loginUrl()) {
  if (getToken()) return true;

  document.getElementById("auth-modal")?.remove();
  const modal = document.createElement("div");
  modal.id = "auth-modal";
  modal.innerHTML = `
    <div class="modal-backdrop">
      <div class="modal-card modal-dark">
        <div style="font-size: 45px; margin-bottom: 10px;">🏁</div>
        <h3>${esc(t("auth_title"))}</h3>
        <p>${esc(t("auth_desc"))}</p>
        <div class="modal-actions">
          <button id="auth-cancel-btn" class="btn btn-dark">${esc(t("cancel"))}</button>
          <button id="auth-login-btn" class="btn btn-red">${esc(t("go_to_login"))}</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  document.getElementById("auth-cancel-btn").onclick = () => modal.remove();
  document.getElementById("auth-login-btn").onclick = () => {
    window.location.href = redirectUrl;
  };
  return false;
}

/* ==========================================================
   Auto Init
   ========================================================== */
document.addEventListener("DOMContentLoaded", () => {
  renderHeader();
  renderFooter();
  applyTranslations();
  refreshCurrentUser();
});
