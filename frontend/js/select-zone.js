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
backLink.href = `race-detail.html?id=${raceId}`;

let zones = [];
let selectedZone = null;
let quantity = 1;

function renderZones() {
  zoneListEl.innerHTML = zones
    .map((zone) => {
      const soldOut = zone.available_seats <= 0;
      const isSelected = selectedZone && selectedZone.id === zone.id;
      return `
        <div class="zone-card ${isSelected ? "selected" : ""} ${soldOut ? "disabled" : ""}" data-zone-id="${zone.id}">
          <div>
            <div class="zone-name">${zone.name}</div>
            <div class="zone-seats">${soldOut ? "ตั๋วหมดแล้ว" : `เหลือ ${zone.available_seats} ที่นั่ง`}</div>
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
    qtySection.style.display = "none";
    confirmBtn.disabled = true;
    return;
  }

  // จำกัดจำนวนตั๋วไม่ให้เกินที่นั่งคงเหลือ (edge case: ที่นั่งเหลือน้อยกว่าที่กำลังจะเลือก)
  const maxQty = Math.min(selectedZone.available_seats, 10);
  if (quantity > maxQty) quantity = maxQty;
  if (quantity < 1) quantity = 1;

  qtySection.style.display = "block";
  qtyValueEl.textContent = quantity;
  summaryZoneEl.textContent = selectedZone.name;
  summaryPriceEl.textContent = formatPrice(selectedZone.price);
  summaryTotalEl.textContent = formatPrice(selectedZone.price * quantity);
  confirmBtn.disabled = false;
}

document.getElementById("qty-minus").addEventListener("click", () => {
  quantity -= 1;
  updateSummary();
});

document.getElementById("qty-plus").addEventListener("click", () => {
  quantity += 1;
  updateSummary();
});

confirmBtn.addEventListener("click", async () => {
  if (!selectedZone) return;
  confirmBtn.disabled = true;
  confirmBtn.textContent = "กำลังล็อกที่นั่ง...";
  errorBox.innerHTML = "";

  try {
    const booking = await BookingAPI.create(Number(raceId), selectedZone.id, quantity);
    saveState({ raceId: Number(raceId), bookingId: booking.id });
    window.location.href = `checkout.html?booking_id=${booking.id}`;
  } catch (err) {
    showError(errorBox, err.message);
    confirmBtn.disabled = false;
    confirmBtn.textContent = "ล็อกที่นั่งชั่วคราว →";
  }
});

async function loadZones() {
  if (!raceId) {
    showError(zoneListEl, "ไม่พบรหัสรายการแข่งขัน กรุณากลับไปเลือกใหม่");
    return;
  }
  try {
    zones = await RaceAPI.getZones(raceId);
    renderZones();
  } catch (err) {
    showError(zoneListEl, err.message);
  }
}

loadZones();
