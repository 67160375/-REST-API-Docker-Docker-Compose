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

// 🔘 ปุ่มกดจองตั๋ว
if (confirmBtn) {
  confirmBtn.addEventListener("click", async () => {
    if (!selectedZone) {
      const alertMsg = getCurrentLang() === "en" ? "Please select a zone first." : "กรุณาเลือกโซนที่นั่งก่อนครับ";
      alert(alertMsg);
      return;
    }

    if (!requireAuth()) return;

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
      showError(errorBox || zoneListEl, err.message);
      confirmBtn.disabled = false;
      confirmBtn.textContent = t("confirm_zone_btn");
    }
  });
}

async function loadZones() {
  if (!raceId) {
    showError(zoneListEl, t("err_no_race_id"));
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