/* ==========================================================
   races.js — หน้าค้นหารายการแข่งขัน (/races)
   ========================================================== */

const raceGrid = document.getElementById("race-grid");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");

function renderRaceCards(races) {
  if (!races || !races.length) {
    const emptyMsg = typeof t === "function" && t("no_races_found") !== "no_races_found"
      ? t("no_races_found")
      : (getCurrentLang() === "en" ? "No races found matching your search." : "ไม่พบรายการแข่งขันที่ตรงกับคำค้นหา");

    raceGrid.innerHTML = `<div class="empty-state" style="text-align: center; color: #888; padding: 40px 0;">${emptyMsg}</div>`;
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
          <div class="price">${t("from_price")} ${formatPrice(race.price_from || race.price || 0)}</div>
        </div>
      </a>
    `
    )
    .join("");
}

async function loadRaces(keyword) {
  const loadingMsg = typeof t === "function" && t("loading_races") !== "loading_races"
    ? t("loading_races")
    : (getCurrentLang() === "en" ? "Loading races..." : "กำลังโหลดรายการแข่งขัน...");

  raceGrid.innerHTML = `<div class="skeleton">${loadingMsg}</div>`;
  
  try {
    const races = await RaceAPI.listRaces(keyword);
    renderRaceCards(races);
  } catch (err) {
    showError(raceGrid, err.message);
  }
}

if (searchBtn) {
  searchBtn.addEventListener("click", () => loadRaces(searchInput.value));
}

if (searchInput) {
  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadRaces(searchInput.value);
  });
}

loadRaces();