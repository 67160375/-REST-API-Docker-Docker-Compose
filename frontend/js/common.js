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

window.toggleLanguage = function() {
  const current = getCurrentLang();
  const nextLang = current === "th" ? "en" : "th";
  localStorage.setItem("app_lang", nextLang);
  window.location.reload();
};

/* ==========================================================
   🌐 ฟังก์ชันกวาดแปลภาษาอัตโนมัติทั้ง DOM (รองรับ text, placeholder, value)
   ========================================================== */
function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    el.placeholder = t(key);
  });
  document.querySelectorAll("[data-i18n-value]").forEach((el) => {
    const key = el.getAttribute("data-i18n-value");
    el.value = t(key);
  });
}

/* ==========================================================
   Header & Footer
   ========================================================== */
function renderHeader(activeHref = "") {
  const header = document.createElement("header");
  header.className = "site-header";
  
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  let authHtml = '';

  const isLoggedIn = token && token !== "null" && token !== "undefined" && token.trim() !== "";
  const currentLangDisplay = getCurrentLang().toUpperCase();

  if (isLoggedIn && userStr) {
      try {
        const user = JSON.parse(userStr);
        authHtml = `
          <div style="display: inline-flex; align-items: center; gap: 15px; font-size: 14px;">
            <span style="color: white;">${t('welcome')}, <strong>${user.username}</strong></span>
            <a href="/pages/auth.html" style="color: white; text-decoration: underline;">${t('account')}</a>
            <button onclick="handleMainLogout()" style="padding: 6px 12px; background: #d32f2f; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">${t('logout')}</button>
          </div>
        `;
      } catch(e) {
        authHtml = `<a href="/pages/auth.html" style="padding: 8px 16px; background: #e50914; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">${t('login_btn')}</a>`;
      }
  } else {
      authHtml = `
        <a href="/pages/auth.html" style="padding: 8px 16px; background: #e50914; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">${t('login_btn')}</a>
      `;
  }

  header.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; max-width: 1200px; margin: 0 auto; padding: 10px 20px; flex-wrap: wrap;">
        <a href="/pages/races.html" class="logo" style="text-decoration: none; font-size: 20px; font-weight: bold; color: white;">
          <span class="flag">🏁</span> Grid Pass
        </a>
        <nav style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
          <a href="/pages/races.html" style="text-decoration: none; color: white; font-weight: bold;">${t('races')}</a>
          ${authHtml}
          <button onclick="toggleLanguage()" style="
            background: #e50914; color: #fff; border: 1px solid #fff; 
            padding: 5px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 13px;
          ">🌐 ${currentLangDisplay}</button>
        </nav>
    </div>
  `;
  document.body.prepend(header);
}

window.handleMainLogout = function() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.reload(); 
};

function renderFooter() {
  const footer = document.createElement("footer");
  footer.className = "site-footer";
  footer.innerHTML = `&copy; 2026 ${t('footer')}`;
  document.body.appendChild(footer);
}

/* ==========================================================
   State & Utility Functions
   ========================================================== */
function saveState(partial) {
  const current = getState();
  const next = { ...current, ...partial };
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
  return `${formattedNum} ${t('currency')}`;
}

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function showError(container, message) {
  if (container) {
    container.innerHTML = `<div class="alert alert-error">⚠️ ${message}</div>`;
  }
}

/* ==========================================================
   🔒 Authentication Check (Modal เตือนธีมสีแดง Grid Pass)
   ========================================================== */
function requireAuth(redirectUrl = "/pages/auth.html") {
  const token = localStorage.getItem("token");

  if (token && token !== "null" && token !== "undefined" && token.trim() !== "") {
    return true;
  }

  const existingModal = document.getElementById("auth-modal");
  if (existingModal) {
    existingModal.remove();
  }

  const modal = document.createElement("div");
  modal.id = "auth-modal";
  modal.innerHTML = `
    <div style="
      position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(0, 0, 0, 0.85); display: flex; align-items: center;
      justify-content: center; z-index: 999999; backdrop-filter: blur(5px);
    ">
      <div style="
        background: #181818; border: 2px solid #e50914; border-radius: 12px;
        padding: 30px; max-width: 400px; width: 90%; text-align: center;
        box-shadow: 0 0 25px rgba(229, 9, 20, 0.5); color: #fff; font-family: sans-serif;
      ">
        <div style="font-size: 45px; margin-bottom: 10px;">🏁</div>
        <h3 style="color: #e50914; margin: 0 0 10px 0; font-size: 1.5rem; letter-spacing: 1px;">${t('auth_title')}</h3>
        <p style="color: #ccc; margin: 0 0 25px 0; font-size: 0.95rem; line-height: 1.4;">
          ${t('auth_desc')}
        </p>
        <div style="display: flex; gap: 10px;">
          <button id="auth-cancel-btn" style="
            background: #333; color: #fff; border: 1px solid #555; padding: 10px 15px;
            border-radius: 6px; font-weight: bold; cursor: pointer; flex: 1;
          ">${t('cancel')}</button>
          <button id="auth-login-btn" style="
            background: #e50914; color: #fff; border: none; padding: 10px 15px;
            border-radius: 6px; font-weight: bold; cursor: pointer; flex: 1;
          ">${t('go_to_login')}</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  document.getElementById("auth-cancel-btn").onclick = () => {
    modal.remove();
  };
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
});