/* ==========================================================
   schedule.js — หน้าตารางการแข่ง (/schedule)
   ไม่ระบุ ?id= : แสดงทุกรายการเรียงตามวันที่ (1 รายการ = 1 วัน)
   ระบุ ?id=    : แสดงเฉพาะรายการนั้น
   ========================================================== */

const scheduleContent = document.getElementById("schedule-content");
const filterBar = document.getElementById("filter-bar");
const onlyRaceId = getQueryParam("id");

let races = [];
let activeFilter = "";

const THAI_DAYS = ["อาทิตย์", "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์"];
const EN_DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

function dayName(raceDate) {
  const [d, m, y] = String(raceDate).split("/").map(Number);
  if (!d || !m || !y) return "";
  const day = new Date(y, m - 1, d).getDay();
  return (getCurrentLang() === "en" ? EN_DAYS : THAI_DAYS)[day];
}

function renderFilters() {
  const categories = [...new Set(races.flatMap((r) => scheduleCategories(r.schedule)))];
  if (categories.length < 2) {
    filterBar.innerHTML = "";
    return;
  }
  const chip = (value, label) =>
    `<button type="button" class="chip ${activeFilter === value ? "active" : ""}" data-filter="${esc(value)}">${esc(label)}</button>`;
  filterBar.innerHTML =
    chip("", getCurrentLang() === "en" ? "All classes" : "ทุกประเภท") + categories.map((c) => chip(c, c)).join("");
  filterBar.querySelectorAll(".chip").forEach((el) =>
    el.addEventListener("click", () => {
      activeFilter = el.dataset.filter;
      renderFilters();
      renderSchedule();
    })
  );
}

function renderSchedule() {
  const shown = races.filter((r) => !activeFilter || r.schedule.some((it) => it.category === activeFilter));
  if (!shown.length) {
    scheduleContent.innerHTML = `<div class="empty-state">ไม่พบรายการที่มีประเภทนี้</div>`;
    return;
  }
  scheduleContent.innerHTML = shown
    .map((race) => {
      const today = isRaceToday(race.race_date);
      const classes = scheduleCategories(race.schedule);
      return `
      <section class="day-card ${today ? "is-today" : ""}">
        <div class="day-head">
          <div class="day-date">
            <span class="day-name">${esc(dayName(race.race_date))}</span>
            <span class="day-num">${esc(race.race_date)}</span>
            ${today ? `<span class="live-badge">วันนี้</span>` : ""}
          </div>
          <div class="day-info">
            <h2>${esc(race.name)}</h2>
            <div class="meta">📍 ${esc(race.venue)}</div>
            <div class="tl-tags">${classes.map((c) => `<span class="class-tag">${esc(c)}</span>`).join("")}</div>
          </div>
          <a class="btn btn-primary btn-sm" href="select-zone.html?id=${encodeURIComponent(race.id)}">จองตั๋ว →</a>
        </div>
        ${renderTimeline(race.schedule, { today, filter: activeFilter })}
      </section>`;
    })
    .join("");
}

async function loadSchedule() {
  try {
    races = await RaceAPI.allSchedules();
    if (onlyRaceId) races = races.filter((r) => String(r.id) === String(onlyRaceId));
    if (!races.length) {
      scheduleContent.innerHTML = `<div class="empty-state">ยังไม่มีตารางการแข่ง</div>`;
      return;
    }
    renderFilters();
    renderSchedule();
  } catch (err) {
    showError(scheduleContent, err.message);
  }
}

loadSchedule();
