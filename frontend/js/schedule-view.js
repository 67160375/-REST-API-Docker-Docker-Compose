/* ==========================================================
   schedule-view.js — วาดตารางเวลาในวันแข่ง (ใช้ร่วมกันหลายหน้า)
   ========================================================== */

const SESSION_TYPES = {
  practice: { th: "ฝึกซ้อม", en: "Practice" },
  qualifying: { th: "จับเวลา", en: "Qualifying" },
  race: { th: "แข่งขัน", en: "Race" },
  activity: { th: "กิจกรรม", en: "Activity" },
};

function sessionLabel(type) {
  const item = SESSION_TYPES[type];
  return item ? item[getCurrentLang()] || item.th : type;
}

function timeRange(item) {
  return item.end_time ? `${item.start_time}–${item.end_time}` : item.start_time;
}

// วันนี้ตรงกับวันแข่งไหม (race_date รูปแบบ dd/mm/yyyy)
function isRaceToday(raceDate) {
  const d = new Date();
  const today = `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
  return raceDate === today;
}

function _toMinutes(hhmm) {
  const [h, m] = String(hhmm || "").split(":").map(Number);
  return h * 60 + (m || 0);
}

function isNow(item) {
  const d = new Date();
  const now = d.getHours() * 60 + d.getMinutes();
  const start = _toMinutes(item.start_time);
  const end = item.end_time ? _toMinutes(item.end_time) : start + 30;
  return now >= start && now < end;
}

/**
 * items: [{start_time, end_time, category, session_type, title, note}]
 * options.today: true = ไฮไลต์รายการที่กำลังแข่งอยู่
 * options.filter: ชื่อประเภทรถที่จะแสดง (ว่าง = ทั้งหมด)
 */
function renderTimeline(items, options = {}) {
  const list = (items || []).filter((it) => !options.filter || it.category === options.filter);
  if (!list.length) {
    return `<p class="muted">${getCurrentLang() === "en" ? "No schedule yet" : "ยังไม่มีตารางเวลา"}</p>`;
  }
  return `
    <ol class="timeline">
      ${list
        .map((it) => {
          const live = options.today && isNow(it);
          return `
          <li class="timeline-item type-${esc(it.session_type)} ${live ? "live" : ""}">
            <div class="tl-time">${esc(timeRange(it))}</div>
            <div class="tl-dot"></div>
            <div class="tl-body">
              <div class="tl-title">
                ${esc(it.title)}
                ${live ? `<span class="live-badge">● ${getCurrentLang() === "en" ? "LIVE" : "กำลังแข่ง"}</span>` : ""}
              </div>
              <div class="tl-tags">
                <span class="session-tag session-${esc(it.session_type)}">${esc(sessionLabel(it.session_type))}</span>
                ${it.session_type !== "activity" ? `<span class="class-tag">${esc(it.category)}</span>` : ""}
              </div>
              ${it.note ? `<div class="tl-note">${esc(it.note)}</div>` : ""}
            </div>
          </li>`;
        })
        .join("")}
    </ol>
  `;
}

// ประเภทรถ/รุ่น ที่มีในตาราง (ไม่นับกิจกรรม) ใช้ทำปุ่มกรอง
function scheduleCategories(items) {
  return [...new Set((items || []).filter((it) => it.session_type !== "activity").map((it) => it.category))];
}
