/* ==========================================================
   select-zone.js — หน้าเลือกโซน & จำนวนตั๋ว (/select-zone)
   - แตะโซนบนภาพผังสนาม หรือเลือกจากรายการ
   - เปิดด้วย ?mapdebug=1 แล้วคลิกบนภาพ จะบอกพิกัด % (ใช้ตั้งตำแหน่งโซนตอนเปลี่ยนภาพจริง)
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
const mapWrap = document.getElementById("venue-map");
const mapImg = document.getElementById("venue-map-img");
const hotspotsEl = document.getElementById("venue-hotspots");
const mapLegend = document.getElementById("map-legend");
const mapDebug = document.getElementById("map-debug");

const raceId = getQueryParam("id");
if (backLink && raceId) backLink.href = `race-detail.html?id=${encodeURIComponent(raceId)}`;

let zones = [];
let selectedZone = null;
let quantity = 1;

function selectZone(zoneId) {
  const zone = zones.find((z) => z.id === zoneId);
  if (!zone || zone.available_seats <= 0) return;
  selectedZone = zone;
  quantity = 1;
  updateSummary();
  renderZones();
  renderHotspots();
}

// จุดเด่นของโซน (description คั่นแต่ละข้อด้วยการขึ้นบรรทัดใหม่)
function zonePerks(zone) {
  return String(zone.description || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function renderHotspots() {
  const placed = zones.filter((z) => z.map_x != null && z.map_y != null && z.map_w != null && z.map_h != null);
  hotspotsEl.innerHTML = placed
    .map((z) => {
      const soldOut = z.available_seats <= 0;
      const selected = selectedZone && selectedZone.id === z.id;
      return `
        <button type="button"
          class="hotspot crowd-${esc(z.crowd_level || "low")} ${selected ? "selected" : ""}"
          style="left:${Number(z.map_x)}%;top:${Number(z.map_y)}%;width:${Number(z.map_w)}%;height:${Number(z.map_h)}%;"
          data-zone-id="${z.id}" ${soldOut ? "disabled" : ""}
          title="${esc([`${z.name} • ${formatPrice(z.price)} • ${soldOut ? "เต็ม" : `เหลือ ${z.available_seats} ที่`}`, ...zonePerks(z)].join("\n"))}">
          <span class="hotspot-label">${esc(z.name)}<small>${esc(formatPrice(z.price))}</small></span>
        </button>`;
    })
    .join("");
  hotspotsEl.querySelectorAll(".hotspot:not([disabled])").forEach((el) =>
    el.addEventListener("click", () => selectZone(Number(el.dataset.zoneId)))
  );
  if (mapLegend) mapLegend.hidden = placed.length === 0;
}

function renderZones() {
  zoneListEl.innerHTML = zones
    .map((zone) => {
      const soldOut = zone.available_seats <= 0;
      const isSelected = selectedZone && selectedZone.id === zone.id;
      const seatsText = soldOut ? t("sold_out") : t("available_seats", { n: zone.available_seats });
      const crowdBadge = zone.crowd_label
        ? `<span class="crowd-badge crowd-${esc(zone.crowd_level || "low")}"><span class="crowd-dot"></span>${esc(zone.crowd_label)}</span>`
        : "";
      const perks = zonePerks(zone);
      const perksHtml = perks.length
        ? `<ul class="zone-perks">${perks.map((p) => `<li>${esc(p)}</li>`).join("")}</ul>`
        : "";
      return `
        <div class="zone-card ${isSelected ? "selected" : ""} ${soldOut ? "disabled" : ""}" data-zone-id="${zone.id}"
             role="button" tabindex="${soldOut ? -1 : 0}" aria-pressed="${isSelected}">
          <div>
            <div class="zone-name">${esc(zone.name)}</div>
            <div class="zone-seats">${esc(seatsText)}</div>
            ${perksHtml}
            ${crowdBadge}
          </div>
          <div class="zone-price">${formatPrice(zone.price)}</div>
        </div>`;
    })
    .join("");

  zoneListEl.querySelectorAll(".zone-card:not(.disabled)").forEach((el) => {
    const pick = () => selectZone(Number(el.dataset.zoneId));
    el.addEventListener("click", pick);
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        pick();
      }
    });
  });
}

function updateSummary() {
  if (!selectedZone) {
    qtySection.style.display = "none";
    confirmBtn.disabled = true;
    return;
  }
  const maxQty = Math.min(selectedZone.available_seats, 10);
  quantity = Math.max(1, Math.min(quantity, maxQty));

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

// ===== จำสิ่งที่เลือกไว้ ตอนต้องล็อกอินก่อนจอง =====
const PENDING_KEY = "grid_pass_pending_booking";
const PENDING_TTL_MS = 30 * 60 * 1000;

function savePendingSelection() {
  if (!selectedZone) return;
  try {
    sessionStorage.setItem(
      PENDING_KEY,
      JSON.stringify({ raceId: Number(raceId), zoneId: selectedZone.id, quantity, savedAt: Date.now() })
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

function loginRedirectUrl() {
  return loginUrl(`${window.location.pathname}?id=${encodeURIComponent(raceId)}&resume=1`);
}

async function submitBooking() {
  if (!selectedZone) {
    showError(errorBox, getCurrentLang() === "en" ? "Please select a zone first." : "กรุณาเลือกโซนที่นั่งก่อน");
    return;
  }
  if (!getToken()) {
    savePendingSelection();
    requireAuth(loginRedirectUrl());
    return;
  }

  confirmBtn.disabled = true;
  confirmBtn.textContent = t("locking_seats");
  errorBox.innerHTML = "";

  try {
    const booking = await BookingAPI.create(Number(raceId), selectedZone.id, quantity);
    saveState({ raceId: Number(raceId), bookingId: booking.id });
    window.location.href = `checkout.html?booking_id=${encodeURIComponent(booking.id)}`;
  } catch (err) {
    confirmBtn.disabled = false;
    confirmBtn.textContent = t("confirm_zone_btn");
    if (err.status === 401) {
      savePendingSelection();
      requireAuth(loginRedirectUrl());
      return;
    }
    showError(errorBox, err.message);
    loadZones(false); // ดึงที่นั่งล่าสุด เผื่อมีคนจองตัดหน้า
  }
}

confirmBtn.addEventListener("click", submitBooking);

// กลับมาจากหน้าล็อกอิน (?resume=1): คืนค่าที่เลือกไว้ แล้วไปต่อขั้นจองให้เลย
function resumePendingBooking() {
  if (getQueryParam("resume") !== "1") return;
  history.replaceState(null, "", `select-zone.html?id=${encodeURIComponent(raceId)}`);

  const p = takePendingSelection();
  if (!p || !getToken()) return;

  const zone = zones.find((z) => z.id === p.zoneId);
  if (!zone || zone.available_seats < 1) {
    showError(errorBox, "โซนที่คุณเลือกไว้ที่นั่งหมดแล้ว กรุณาเลือกโซนใหม่");
    return;
  }
  selectedZone = zone;
  quantity = Math.min(p.quantity, zone.available_seats, 10);
  updateSummary();
  renderZones();
  renderHotspots();

  if (quantity < p.quantity) {
    showError(errorBox, `ที่นั่งเหลือไม่พอตามที่เลือกไว้ ปรับเป็น ${quantity} ใบ กรุณาตรวจสอบแล้วกดจองอีกครั้ง`);
    return;
  }
  submitBooking();
}

function setupMap(race) {
  if (!race || !race.venue_map_url) return;
  mapImg.src = race.venue_map_url;
  mapWrap.hidden = false;

  if (getQueryParam("mapdebug") === "1") {
    mapDebug.hidden = false;
    mapDebug.textContent = "โหมดหาพิกัด: คลิกมุมซ้ายบน แล้วมุมขวาล่างของอัฒจันทร์";
    let first = null;
    mapWrap.addEventListener("click", (e) => {
      const rect = mapWrap.getBoundingClientRect();
      const x = +(((e.clientX - rect.left) / rect.width) * 100).toFixed(1);
      const y = +(((e.clientY - rect.top) / rect.height) * 100).toFixed(1);
      if (!first) {
        first = { x, y };
        mapDebug.textContent = `มุมซ้ายบน: x=${x}%, y=${y}% — คลิกมุมขวาล่างต่อ`;
      } else {
        const w = +(x - first.x).toFixed(1), h = +(y - first.y).toFixed(1);
        mapDebug.textContent = `map_x=${first.x}, map_y=${first.y}, map_w=${w}, map_h=${h}  → (${first.x}, ${first.y}, ${w}, ${h})`;
        first = null;
      }
    }, true);
  }
}

async function loadZones(withRace = true) {
  if (!raceId) {
    showError(zoneListEl, t("err_no_race_id"));
    return;
  }
  try {
    const [race, zoneData] = await Promise.all([withRace ? RaceAPI.getRace(raceId) : null, RaceAPI.getZones(raceId)]);
    zones = zoneData;
    if (race) {
      document.getElementById("race-subtitle").textContent = `${race.name} • ${race.race_date} — แตะโซนบนผังสนาม หรือเลือกจากรายการด้านล่าง`;
      setupMap(race);
    }
    if (selectedZone) selectedZone = zones.find((z) => z.id === selectedZone.id && z.available_seats > 0) || null;
    renderZones();
    renderHotspots();
    updateSummary();
    if (withRace) resumePendingBooking();
  } catch (err) {
    showError(zoneListEl, err.message);
  }
}

loadZones();
