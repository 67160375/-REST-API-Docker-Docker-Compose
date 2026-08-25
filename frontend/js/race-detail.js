/* ==========================================================
   race-detail.js — หน้ารายละเอียดการแข่งขัน (/race-detail)
   ========================================================== */

const detailContent = document.getElementById("detail-content");
const raceId = getQueryParam("id");

function renderDetail(race) {
  const activities = race.activities
    .map(
      (a) => `
      <li>
        <span class="time">${a.time}</span>
        <span>${a.title}</span>
      </li>
    `
    )
    .join("");

  detailContent.innerHTML = `
    <div class="detail-hero">
      <div class="thumb">🏁</div>
    </div>

    <span class="category-tag">${race.category}</span>
    <h1 class="page-title">${race.name}</h1>
    <p class="page-subtitle">${race.description || ""}</p>

    <div class="info-card">
      <h2>ตารางเวลา</h2>
      <div class="info-row"><span class="label">วันที่จัดงาน</span><span>${race.race_date}</span></div>
      <div class="info-row"><span class="label">สถานที่</span><span>${race.venue}</span></div>
      <div class="info-row"><span class="label">ราคาเริ่มต้น</span><span>${formatPrice(race.price_from)}</span></div>
    </div>

    <div class="info-card">
      <h2>กิจกรรมในงาน</h2>
      <ul class="activity-list">${activities}</ul>
    </div>

    <div class="info-card">
      <h2>ผังสนาม (Venue Map)</h2>
      <img src="${race.venue_map_url}" alt="ผังสนาม ${race.name}" style="border-radius: 12px; border: 1px solid #ececec;" />
    </div>

    <button class="btn btn-primary btn-block" id="select-zone-btn">เลือกโซนที่นั่ง →</button>
  `;

  document.getElementById("select-zone-btn").addEventListener("click", () => {
    saveState({ raceId: race.id });
    window.location.href = `select-zone.html?id=${race.id}`;
  });
}

async function loadDetail() {
  if (!raceId) {
    showError(detailContent, "ไม่พบรหัสรายการแข่งขัน กรุณากลับไปเลือกใหม่");
    return;
  }
  try {
    const race = await RaceAPI.getRace(raceId);
    renderDetail(race);
  } catch (err) {
    showError(detailContent, err.message);
  }
}

loadDetail();
