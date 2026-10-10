/* ==========================================================
   select-zone.js — หน้าเลือกโซน & จำนวนตั๋ว (/select-zone)
   ========================================================== */

const zoneListEl = document.getElementById("zone-list");
const qtySection = document.getElementById("qty-section");
const qtyValueEl = document.getElementById("qty-value");
const summaryZoneEl = document.getElementById("summary-zone");
const summaryPriceEl = document.getElementById("summary-price");
const summaryTotalEl = document.getElementById("summary-total");
const confirmBtn = document.getElementById("confirm-zone-btn");
const errorBox = document.getElementById("error-box");
const backLink = document.getElementById("back-link");

const raceId = getQueryParam("id");
if (backLink && raceId) {
  backLink.href = `race-detail.html?id=${raceId}`;
}

let zones = [];
let selectedZone = null;
let quantity = 1;

function renderZones() {
  if (!zoneListEl) return;

  zoneListEl.innerHTML = zones
    .map((zone) => {
      const soldOut = zone.available_seats <= 0;
      const isSelected = selectedZone && selectedZone.id === zone.id;

      // 🌐 แปลภาษาจำนวนที่นั่งคงเหลือ
      const seatsText = soldOut
        ? t("sold_out")
        : t("available_seats", { n: zone.available_seats });

      // 🆕 Stand Crowd Status badge — ใช้ crowd_level / crowd_label จาก backend โดยตรง
      const crowdLevel = zone.crowd_level || "low";
      const crowdLabel = zone.crowd_label || "";
      const crowdBadge = crowdLabel
        ? `<span class="crowd-badge crowd-${crowdLevel}"><span class="crowd-dot"></span>${crowdLabel}</span>`
        : "";

      return `
        <div class="zone-card ${isSelected ? "selected" : ""} ${soldOut ? "disabled" : ""}" data-zone-id="${zone.id}">
          <div>
            <div class="zone-name">${zone.name}</div>
            <div class="zone-seats">${seatsText}</div>
            ${crowdBadge}
          </div>
          <div class="zone-price">${formatPrice(zone.price)}</div>
        </div>
      `;
    })
    .join("");

  zoneListEl.querySelectorAll(".zone-card:not(.disabled)").forEach((el) => {
    el.addEventListener("click", () => {
      const zoneId = Number(el.dataset.zoneId);
      selectedZone = zones.find((z) => z.id === zoneId);
      quantity = 1;
      updateSummary();
      renderZones();
    });
  });
}

function updateSummary() {
  if (!selectedZone) {
    if (qtySection) qtySection.style.display = "none";
    if (confirmBtn) confirmBtn.disabled = true;
    return;
  }

  const maxQty = Math.min(selectedZone.available_seats, 10);
  if (quantity > maxQty) quantity = maxQty;
  if (quantity < 1) quantity = 1;

  if (qtySection) qtySection.style.display = "block";
  if (qtyValueEl) qtyValueEl.textContent = quantity;
  if (summaryZoneEl) summaryZoneEl.textContent = selectedZone.name;
  if (summaryPriceEl) summaryPriceEl.textContent = formatPrice(selectedZone.price);
  if (summaryTotalEl) summaryTotalEl.textContent = formatPrice(selectedZone.price * quantity);
  if (confirmBtn) confirmBtn.disabled = false;
}

// ➕➖ ปุ่มเพิ่ม/ลด จำนวนตั๋ว
const qtyMinusBtn = document.getElementById("qty-minus");
if (qtyMinusBtn) {
  qtyMinusBtn.addEventListener("click", () => {
    if (quantity > 1) {
      quantity -= 1;
      updateSummary();
    }
  });
}

const qtyPlusBtn = document.getElementById("qty-plus");
if (qtyPlusBtn) {
  qtyPlusBtn.addEventListener("click", () => {
    quantity += 1;
    updateSummary();
  });
}

// ===== จำสิ่งที่เลือกไว้ ตอนต้องล็อกอินก่อนจอง =====
const PENDING_KEY = "grid_pass_pending_booking";
const PENDING_TTL_MS = 30 * 60 * 1000; // เก็บไว้ไม่เกิน 30 นาที

function hasToken() {
  const tk = localStorage.getItem("token");
  return !!tk && tk !== "null" && tk !== "undefined" && tk.trim() !== "";
}

function savePendingSelection() {
  if (!selectedZone) return;
  try {
    sessionStorage.setItem(
      PENDING_KEY,
      JSON.stringify({
        raceId: Number(raceId),
        zoneId: selectedZone.id,
        quantity: quantity,
        savedAt: Date.now(),
      })
    );
  } catch (e) {}
}

function takePendingSelection() {
  try {
    const raw = sessionStorage.getItem(PENDING_KEY);
    if (!raw) return null;
    sessionStorage.removeItem(PENDING_KEY);
    const p = JSON.parse(raw);
    if (!p || p.raceId !== Number(raceId) || Date.now() - p.savedAt > PENDING_TTL_MS) return null;
    return p;
  } catch (e) {
    return null;
  }
}

// ล็อกอินเสร็จให้กลับมาหน้านี้พร้อม resume=1 เพื่อไปต่ออัตโนมัติ
function loginRedirectUrl() {
  const next = `${window.location.pathname}?id=${raceId}&resume=1`;
  return `/pages/auth.html?next=${encodeURIComponent(next)}`;
}

// 🔘 จองตั๋ว (ถ้ายังไม่ล็อกอิน: จำที่เลือกไว้ แล้วพาไปล็อกอิน)
async function submitBooking() {
  if (!selectedZone) {
    const alertMsg = getCurrentLang() === "en" ? "Please select a zone first." : "กรุณาเลือกโซนที่นั่งก่อนครับ";
    alert(alertMsg);
    return;
  }

  if (!hasToken()) {
    savePendingSelection();
    requireAuth(loginRedirectUrl());
    return;
  }

  confirmBtn.disabled = true;
  confirmBtn.textContent = t("locking_seats");
  if (errorBox) errorBox.innerHTML = "";

  try {
    const booking = await BookingAPI.create(Number(raceId), selectedZone.id, quantity);
    saveState({
      raceId: Number(raceId),
      bookingId: booking.id,
      zone: selectedZone,
      quantity: quantity
    });
    window.location.href = `checkout.html?booking_id=${booking.id}`;
  } catch (err) {
    confirmBtn.disabled = false;
    confirmBtn.textContent = t("confirm_zone_btn");
    if (err.status === 401) {
      // token หมดอายุ/ใช้ไม่ได้ (api.js ล้างให้แล้ว) -> จำที่เลือกไว้ แล้วให้ล็อกอินใหม่
      savePendingSelection();
      requireAuth(loginRedirectUrl());
      return;
    }
    showError(errorBox || zoneListEl, err.message);
  }
}

if (confirmBtn) {
  confirmBtn.addEventListener("click", submitBooking);
}

// กลับมาจากหน้าล็อกอิน (?resume=1): คืนค่าที่เลือกไว้ แล้วไปต่อขั้นจองให้เลย
function resumePendingBooking() {
  if (getQueryParam("resume") !== "1") return;
  history.replaceState(null, "", `select-zone.html?id=${raceId}`); // กันทำซ้ำตอนรีเฟรช

  const p = takePendingSelection();
  if (!p || !hasToken()) return;

  const zone = zones.find((z) => z.id === p.zoneId);
  const box = errorBox || zoneListEl;
  if (!zone || zone.available_seats < 1) {
    showError(box, "โซนที่คุณเลือกไว้ที่นั่งหมดแล้ว กรุณาเลือกโซนใหม่");
    return;
  }

  selectedZone = zone;
  quantity = Math.min(p.quantity, zone.available_seats, 10);
  updateSummary();
  renderZones();

  if (quantity < p.quantity) {
    // ที่นั่งเหลือน้อยกว่าที่เลือกไว้ ไม่จองให้เอง ให้ผู้ใช้ตรวจจำนวนก่อน
    showError(box, `ที่นั่งเหลือไม่พอตามที่เลือกไว้ ปรับเป็น ${quantity} ใบ กรุณาตรวจสอบแล้วกดจองอีกครั้ง`);
    return;
  }
  submitBooking();
}

async function loadZones() {
  if (!raceId) {
    showError(zoneListEl, t("err_no_race_id"));
    return;
  }
  try {
    zones = await RaceAPI.getZones(raceId);
    renderZones();
    resumePendingBooking();
  } catch (err) {
    showError(zoneListEl, err.message);
  }
}

loadZones();