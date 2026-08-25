/* ==========================================================
   races.js — หน้าค้นหารายการแข่งขัน (/races)
   ========================================================== */

const raceGrid = document.getElementById("race-grid");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");

function renderRaceCards(races) {
  if (!races.length) {
    raceGrid.innerHTML = `<div class="empty-state">ไม่พบรายการแข่งขันที่ตรงกับคำค้นหา</div>`;
    return;
  }

  raceGrid.innerHTML = races
    .map(
      (race) => `
      <a class="race-card" href="race-detail.html?id=${race.id}">
        <div class="thumb">🏎️</div>
        <div class="body">
          <span class="category-tag">${race.category}</span>
          <h3>${race.name}</h3>
          <div class="meta">📅 ${race.race_date}</div>
          <div class="meta">📍 ${race.venue}</div>
          <div class="price">เริ่มต้น ${formatPrice(race.price_from)}</div>
        </div>
      </a>
    `
    )
    .join("");
}

async function loadRaces(keyword) {
  raceGrid.innerHTML = `<div class="skeleton">กำลังโหลดรายการแข่งขัน...</div>`;
  try {
    const races = await RaceAPI.listRaces(keyword);
    renderRaceCards(races);
  } catch (err) {
    showError(raceGrid, err.message);
  }
}

searchBtn.addEventListener("click", () => loadRaces(searchInput.value));
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") loadRaces(searchInput.value);
});

loadRaces();
