/* ==========================================================
   race-detail.js — หน้ารายละเอียดการแข่งขัน (/race-detail)
   ========================================================== */

const detailContent = document.getElementById("detail-content");
const raceId = getQueryParam("id");

function tr(key, fallback) {
  const v = t(key);
  return v !== key ? v : fallback;
}

function renderDetail(race) {
  const today = isRaceToday(race.race_date);
  detailContent.innerHTML = `
    <div class="detail-hero">
      <div class="thumb">🏁</div>
    </div>

    <span class="category-tag">${esc(race.category)}</span>
    <h1 class="page-title">${esc(race.name)}</h1>
    <p class="page-subtitle">${esc(race.description || "")}</p>

    <div class="info-card">
      <h2>${getCurrentLang() === "en" ? "Event Info" : "ข้อมูลงาน"}</h2>
      <div class="info-row">
        <span class="label">${esc(tr("race_date", "วันที่จัดงาน"))}</span>
        <span>${esc(race.race_date)}${today ? ' <span class="live-badge">วันนี้</span>' : ""}</span>
      </div>
      <div class="info-row">
        <span class="label">${esc(tr("venue", "สถานที่"))}</span>
        <span>${esc(race.venue)}</span>
      </div>
      <div class="info-row">
        <span class="label">${esc(tr("from_price", "ราคาเริ่มต้น"))}</span>
        <span>${formatPrice(race.price_from)}</span>
      </div>
    </div>

    <div class="info-card">
      <div class="card-head">
        <h2>${esc(t("schedule"))}</h2>
        <a class="link-more" href="schedule.html?id=${encodeURIComponent(race.id)}">${getCurrentLang() === "en" ? "Full schedule →" : "ดูตารางเต็ม →"}</a>
      </div>
      ${renderTimeline(race.schedule, { today })}
    </div>

    ${race.venue_map_url ? `
    <div class="info-card">
      <h2>${esc(tr("venue_map", "ผังสนาม (Venue Map)"))}</h2>
      <img class="venue-map-img" src="${esc(race.venue_map_url)}" alt="ผังสนาม ${esc(race.name)}" />
    </div>` : ""}

    <button class="btn btn-primary btn-block" id="select-zone-btn">${esc(tr("select_zone_btn", "เลือกโซนที่นั่ง →"))}</button>
  `;

  document.getElementById("select-zone-btn").addEventListener("click", () => {
    saveState({ raceId: race.id });
    window.location.href = `select-zone.html?id=${encodeURIComponent(race.id)}`;
  });
}

async function loadDetail() {
  if (!raceId) {
    showError(detailContent, tr("err_no_race_id", "ไม่พบรหัสรายการแข่งขัน กรุณากลับไปเลือกใหม่"));
    return;
  }
  try {
    renderDetail(await RaceAPI.getRace(raceId));
  } catch (err) {
    showError(detailContent, err.message);
  }
}

loadDetail();
