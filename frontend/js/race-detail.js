/* ==========================================================
   race-detail.js — หน้ารายละเอียดการแข่งขัน (/race-detail)
   ========================================================== */

const detailContent = document.getElementById("detail-content");
const raceId = getQueryParam("id");

function renderDetail(race) {
  // ดึงรายการกิจกรรม (ถ้าไม่มีให้แสดงเป็นรายการว่าง)
  const activitiesList = race.activities || [];
  const activitiesHtml = activitiesList.length > 0
    ? activitiesList
        .map(
          (a) => `
          <li>
            <span class="time">${a.time}</span>
            <span>${a.title}</span>
          </li>
        `
        )
        .join("")
    : `<li><span>${t("no_activities") !== "no_activities" ? t("no_activities") : "ไม่มีข้อมูลกิจกรรม"}</span></li>`;

  detailContent.innerHTML = `
    <div class="detail-hero">
      <div class="thumb">🏁</div>
    </div>

    <span class="category-tag">${race.category}</span>
    <h1 class="page-title">${race.name}</h1>
    <p class="page-subtitle">${race.description || ""}</p>

    <div class="info-card">
      <h2>${t("schedule_title") !== "schedule_title" ? t("schedule_title") : "ตารางเวลา"}</h2>
      <div class="info-row">
        <span class="label">${t("race_date") !== "race_date" ? t("race_date") : "วันที่จัดงาน"}</span>
        <span>${race.race_date}</span>
      </div>
      <div class="info-row">
        <span class="label">${t("venue") !== "venue" ? t("venue") : "สถานที่"}</span>
        <span>${race.venue}</span>
      </div>
      <div class="info-row">
        <span class="label">${t("from_price") !== "from_price" ? t("from_price") : "ราคาเริ่มต้น"}</span>
        <span>${formatPrice(race.price_from)}</span>
      </div>
    </div>

    <div class="info-card">
      <h2>${t("activities") !== "activities" ? t("activities") : "กิจกรรมในงาน"}</h2>
      <ul class="activity-list">${activitiesHtml}</ul>
    </div>

    <div class="info-card">
      <h2>${t("venue_map") !== "venue_map" ? t("venue_map") : "ผังสนาม (Venue Map)"}</h2>
      <img src="${race.venue_map_url}" alt="${race.name}" style="border-radius: 12px; border: 1px solid #ececec; max-width: 100%; height: auto;" />
    </div>

    <button class="btn btn-primary btn-block" id="select-zone-btn">${t("select_zone_btn") !== "select_zone_btn" ? t("select_zone_btn") : "เลือกโซนที่นั่ง →"}</button>
  `;

  document.getElementById("select-zone-btn").addEventListener("click", () => {
    saveState({ raceId: race.id });
    window.location.href = `select-zone.html?id=${race.id}`;
  });
}

async function loadDetail() {
  if (!raceId) {
    showError(
      detailContent,
      t("err_no_race_id") !== "err_no_race_id"
        ? t("err_no_race_id")
        : "ไม่พบรหัสรายการแข่งขัน กรุณากลับไปเลือกใหม่"
    );
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