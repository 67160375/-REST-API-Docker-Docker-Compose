/* ==========================================================
   scan.js — หน้าสแกนตั๋วเข้างาน (/scan) สำหรับ staff / admin
   ใช้ BarcodeDetector ของเบราว์เซอร์ถ้ามี ไม่มีก็ใช้ jsQR (vendor/jsQR.js)
   ========================================================== */

const guardEl = document.getElementById("scan-guard");
const appEl = document.getElementById("scan-app");
const video = document.getElementById("scan-video");
const canvas = document.getElementById("scan-canvas");
const idleEl = document.getElementById("scan-idle");
const frameEl = document.getElementById("scan-frame");
const resultEl = document.getElementById("scan-result");
const manualForm = document.getElementById("manual-form");
const manualCode = document.getElementById("manual-code");

let stream = null;
let detector = null;
let paused = false; // หยุดสแกนระหว่างแสดงผล กันอ่าน QR เดิมซ้ำรัวๆ
let busy = false;

const RESULT_STYLE = {
  ok: { icon: "✅", cls: "ok" },
  already_used: { icon: "⛔", cls: "bad" },
  not_found: { icon: "❓", cls: "bad" },
  not_paid: { icon: "💸", cls: "bad" },
  wrong_day: { icon: "📅", cls: "warn" },
};

function beep(ok) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    osc.frequency.value = ok ? 880 : 220;
    osc.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + (ok ? 0.15 : 0.4));
  } catch (e) {}
}

function renderResult(r, code) {
  const style = RESULT_STYLE[r.result] || { icon: "⚠️", cls: "bad" };
  resultEl.innerHTML = `
    <div class="scan-result ${style.cls}">
      <div class="scan-icon">${style.icon}</div>
      <div class="scan-message">${esc(r.message)}</div>
      ${r.date_warning ? `<div class="scan-sub">${esc(r.date_warning)}</div>` : ""}
      ${r.ticket_code ? `
        <div class="scan-details">
          <div><span>ตั๋ว</span><strong>${esc(r.ticket_code)}</strong></div>
          <div><span>รายการ</span>${esc(r.race_name || "-")} (${esc(r.race_date || "-")})</div>
          <div><span>โซน</span><strong>${esc(r.zone_name || "-")}</strong> × ${esc(r.quantity ?? "-")} คน</div>
          <div><span>ชื่อ</span>${esc(r.buyer_name || "-")}</div>
        </div>` : ""}
      <div class="btn-row">
        ${r.result === "wrong_day" ? `<button type="button" class="btn btn-danger" id="force-btn">ยืนยันให้เข้างาน</button>` : ""}
        <button type="button" class="btn btn-primary" id="next-btn">สแกนคนถัดไป</button>
      </div>
    </div>`;
  beep(r.result === "ok");

  document.getElementById("next-btn").addEventListener("click", resume);
  const force = document.getElementById("force-btn");
  if (force) force.addEventListener("click", () => submitCode(code, true));
}

function resume() {
  resultEl.innerHTML = "";
  manualCode.value = "";
  paused = false;
}

async function submitCode(code, force = false) {
  if (busy) return;
  busy = true;
  paused = true;
  try {
    renderResult(await CheckInAPI.scan(code, force), code);
  } catch (err) {
    if (err.status === 401 || err.status === 403) return showGuard();
    renderResult({ result: "error", message: err.message }, code);
  } finally {
    busy = false;
  }
}

async function scanLoop() {
  if (!stream) return;
  if (!paused && !busy && video.readyState >= 2) {
    let text = null;
    try {
      if (detector) {
        const codes = await detector.detect(video);
        if (codes.length) text = codes[0].rawValue;
      } else if (typeof jsQR === "function") {
        const w = video.videoWidth, h = video.videoHeight;
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d", { willReadFrequently: true });
        ctx.drawImage(video, 0, 0, w, h);
        const found = jsQR(ctx.getImageData(0, 0, w, h).data, w, h, { inversionAttempts: "dontInvert" });
        if (found) text = found.data;
      }
    } catch (e) {
      /* เฟรมนี้อ่านไม่ได้ ข้ามไป */
    }
    if (text) submitCode(text.trim());
  }
  setTimeout(() => requestAnimationFrame(scanLoop), 150);
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    showError(resultEl, "เบราว์เซอร์นี้เปิดกล้องไม่ได้ (ต้องเปิดผ่าน https หรือ localhost) ใช้ช่องพิมพ์รหัสแทนได้");
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
  } catch (err) {
    showError(resultEl, `เปิดกล้องไม่ได้: ${err.message}`);
    return;
  }
  if ("BarcodeDetector" in window) {
    try {
      const formats = await BarcodeDetector.getSupportedFormats();
      if (formats.includes("qr_code")) detector = new BarcodeDetector({ formats: ["qr_code"] });
    } catch (e) {}
  }
  video.srcObject = stream;
  await video.play();
  video.hidden = false;
  frameEl.hidden = false;
  idleEl.hidden = true;
  scanLoop();
}

document.getElementById("start-camera").addEventListener("click", startCamera);
manualForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const code = manualCode.value.trim();
  if (code.length >= 3) submitCode(code);
});

function showGuard() {
  appEl.hidden = true;
  if (stream) stream.getTracks().forEach((tr) => tr.stop());
  stream = null;
  guardEl.innerHTML = `
    <div class="state-card closed">
      <div class="state-icon">🔒</div>
      <h1>หน้านี้สำหรับพนักงานหน้างาน (staff) หรือแอดมินเท่านั้น</h1>
      <a class="btn btn-primary" href="${loginUrl()}">เข้าสู่ระบบ</a>
    </div>`;
}

const me = getUser();
if (!getToken() || !me || !["staff", "admin"].includes(me.role)) showGuard();
else appEl.hidden = false;
