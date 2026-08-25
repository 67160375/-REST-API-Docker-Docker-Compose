/* ==========================================================
   common.js
   ฟังก์ชันช่วยเหลือที่ใช้ร่วมกันทุกหน้า
   ========================================================== */

const STORAGE_KEY = "Grid_Pass_state";

function renderHeader(activeHref = "") {
  const header = document.createElement("header");
  header.className = "site-header";
  
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  let authHtml = '';

  if (token && userStr) {
      const user = JSON.parse(userStr);
      authHtml = `
        <div style="display: inline-flex; align-items: center; gap: 15px; font-size: 14px;">
          <span style="color: white;">ยินดีต้อนรับ, <strong>${user.username}</strong></span>
          <a href="/pages/auth.html" style="color: white; text-decoration: underline;">จัดการบัญชี</a>
          <button onclick="handleMainLogout()" style="padding: 6px 12px; background: #d32f2f; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">ออกจากระบบ</button>
        </div>
      `;
  } else {
      authHtml = `
        <a href="/pages/auth.html" style="padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">เข้าสู่ระบบ / สมัครสมาชิก</a>
      `;
  }

  header.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; max-width: 1200px; margin: 0 auto; padding: 10px 20px;">
        <a href="/pages/races.html" class="logo" style="text-decoration: none; font-size: 20px; font-weight: bold; color: white;">
          <span class="flag">🏁</span> Grid Pass
        </a>
        <nav style="display: flex; align-items: center; gap: 20px;">
          <a href="/pages/races.html" style="text-decoration: none; color: white; font-weight: bold;">รายการแข่งขัน</a>
          ${authHtml}
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
  footer.innerHTML = `&copy; 2026 Grid Pass — ระบบจองตั๋วชมการแข่งขันรถ (เดโม)`;
  document.body.appendChild(footer);
}

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
  return Number(number).toLocaleString("th-TH") + " บาท";
}

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function showError(container, message) {
  container.innerHTML = `<div class="alert alert-error">⚠️ ${message}</div>`;
}

document.addEventListener("DOMContentLoaded", () => {
  renderHeader();
  renderFooter();
});