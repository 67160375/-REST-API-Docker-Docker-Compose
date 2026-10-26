/* ==========================================================
   admin.js — หน้าแอดมินตรวจสลิป (/admin)
   ทุกการกระทำถูกตรวจสิทธิ์ที่ backend อีกชั้น (หน้านี้ซ่อน/แสดงเพื่อความสะดวกเท่านั้น)
   ========================================================== */

const guardEl = document.getElementById("admin-guard");
const appEl = document.getElementById("admin-app");
const statsEl = document.getElementById("stats");
const warningsEl = document.getElementById("config-warnings");
const queueList = document.getElementById("queue-list");
const queueCount = document.getElementById("queue-count");
const queueUpdated = document.getElementById("queue-updated");
const allTable = document.getElementById("all-table");
const statusFilter = document.getElementById("status-filter");
const seatsContent = document.getElementById("seats-content");

const rejectModal = document.getElementById("reject-modal");
const rejectForm = document.getElementById("reject-form");
const rejectReason = document.getElementById("reject-reason");
const rejectOther = document.getElementById("reject-other");
const rejectError = document.getElementById("reject-error");
const slipModal = document.getElementById("slip-modal");
const slipModalImg = document.getElementById("slip-modal-img");

const REFRESH_MS = 15000;
const slipUrls = new Map(); // booking_id -> objectURL (ไม่ต้องโหลดรูปซ้ำทุกรอบ)
let activeTab = "queue";
let rejectTarget = null;
let refreshTimer = null;
let lastSummary = null;

/* ---------------- utilities ---------------- */
async function slipUrl(id) {
  if (!slipUrls.has(id)) slipUrls.set(id, URL.createObjectURL(await AdminAPI.slip(id)));
  return slipUrls.get(id);
}

function modalOpen() {
  return !rejectModal.hidden || !slipModal.hidden;
}

// ข้อความแจ้งผลชั่วคราว (อยู่นอกรายการ จะได้ไม่ถูกล้างตอนรีเฟรชรายการ)
const flashEl = document.getElementById("admin-flash");
function flash(_container, message, kind = "success") {
  const el = document.createElement("div");
  el.className = `alert alert-${kind} flash`;
  el.textContent = message;
  flashEl.prepend(el);
  setTimeout(() => el.remove(), 5000);
}

/* ---------------- summary ---------------- */
function renderSummary(s) {
  lastSummary = s;
  const c = s.counts;
  statsEl.innerHTML = `
    <div class="stat ${s.pending_review ? "stat-alert" : ""}"><span class="stat-num">${s.pending_review}</span><span>รอตรวจสลิป</span></div>
    <div class="stat"><span class="stat-num">${c.paid || 0}</span><span>ชำระแล้ว (รายการ)</span></div>
    <div class="stat"><span class="stat-num">${formatPrice(s.paid_revenue)}</span><span>ยอดขายที่อนุมัติแล้ว</span></div>
    <div class="stat"><span class="stat-num">${(c.pending || 0) + (c.awaiting_payment || 0) + (c.rejected || 0)}</span><span>กำลังจอง / รอโอน</span></div>`;

  const warnings = [];
  if (!s.promptpay_configured) warnings.push("ยังไม่ได้ตั้งค่าเลขพร้อมเพย์ (PROMPTPAY_ID ในไฟล์ .env) — ลูกค้าจะชำระเงินไม่ได้");
  if (s.slip_verify_provider && s.slip_verify_provider !== "none")
    warnings.push(`เปิดตรวจสลิปอัตโนมัติ (${s.slip_verify_provider}) — รายการที่ผ่านจะอนุมัติเอง ที่เหลือจะมาอยู่ในคิวนี้`);
  warningsEl.innerHTML = warnings
    .map((w, i) => `<div class="alert ${i === 0 && !s.promptpay_configured ? "alert-error" : "alert-warning"}">${esc(w)}</div>`)
    .join("");

  queueCount.textContent = s.pending_review;
  document.title = `${s.pending_review ? `(${s.pending_review}) ` : ""}แอดมิน | Grid Pass`;
  renderSeats(s);
}

function renderSeats(s) {
  seatsContent.innerHTML = s.races
    .map(
      (r) => `
      <div class="info-card">
        <h2>${esc(r.name)} <span class="muted small">${esc(r.race_date)}</span></h2>
        <div class="table-wrap"><table class="data-table">
          <thead><tr><th>โซน</th><th>ราคา</th><th>ทั้งหมด</th><th>ขายแล้ว</th><th>กำลังจอง</th><th>ว่าง</th></tr></thead>
          <tbody>
            ${r.zones
              .map((z) => {
                const held = z.total_seats - z.available_seats - z.sold_seats;
                return `<tr><td>${esc(z.name)}</td><td>${formatPrice(z.price)}</td><td>${z.total_seats}</td>
                  <td>${z.sold_seats}</td><td>${Math.max(0, held)}</td><td><strong>${z.available_seats}</strong></td></tr>`;
              })
              .join("")}
          </tbody>
        </table></div>
      </div>`
    )
    .join("");
}

/* ---------------- review queue ---------------- */
function reviewCard(b) {
  const dup = b.duplicate_of && b.duplicate_of.length
    ? `<div class="alert alert-error">⚠️ รูปสลิปนี้ซ้ำกับการจอง #${b.duplicate_of.map(esc).join(", #")} — ตรวจสอบให้ดีก่อนอนุมัติ</div>`
    : "";
  const note = b.verify_note ? `<div class="alert alert-warning">🤖 ${esc(b.verify_note)}</div>` : "";
  return `
    <article class="review-card" data-id="${esc(b.id)}">
      <button type="button" class="slip-thumb" data-slip="${esc(b.id)}" title="กดเพื่อดูภาพใหญ่">
        <span class="muted small">กำลังโหลดสลิป...</span>
      </button>
      <div class="review-info">
        <div class="review-top">
          <span class="muted">#${esc(b.id)} • ส่งเมื่อ ${esc(b.slip_uploaded_at || "-")}</span>
        </div>
        <div class="review-amount">${formatPrice(b.total_price)}</div>
        <div class="review-meta">
          <div><span class="label">รายการ</span>${esc(b.race_name)} (${esc(b.race_date)})</div>
          <div><span class="label">โซน</span>${esc(b.zone_name)} × ${b.quantity} ใบ</div>
          <div><span class="label">ผู้ซื้อ</span>${esc(b.buyer_name || "-")} • ${esc(b.buyer_phone || "-")}</div>
          <div><span class="label">บัญชี</span>${esc(b.username || "-")}</div>
        </div>
        ${dup}${note}
        <div class="review-actions">
          <button type="button" class="btn btn-success" data-approve="${esc(b.id)}">✅ อนุมัติ ออกตั๋ว</button>
          <button type="button" class="btn btn-danger-outline" data-reject="${esc(b.id)}">❌ ปฏิเสธ</button>
        </div>
      </div>
    </article>`;
}

async function loadQueue() {
  try {
    const items = await AdminAPI.list("pending_review");
    if (!items.length) {
      queueList.innerHTML = `<div class="empty-state">🎉 ไม่มีสลิปรอตรวจ</div>`;
    } else {
      queueList.innerHTML = items.map(reviewCard).join("");
      bindQueueActions(items);
    }
    queueUpdated.textContent = `อัปเดตล่าสุด ${new Date().toLocaleTimeString("th-TH")} (รีเฟรชเองทุก 15 วินาที)`;
  } catch (err) {
    handleError(err, queueList);
  }
}

function bindQueueActions(items) {
  queueList.querySelectorAll("[data-slip]").forEach(async (el) => {
    const id = el.dataset.slip;
    try {
      const url = await slipUrl(id);
      el.innerHTML = `<img src="${url}" alt="สลิปการจอง #${esc(id)}" />`;
    } catch (err) {
      el.innerHTML = `<span class="muted small">โหลดสลิปไม่ได้: ${esc(err.message)}</span>`;
    }
    el.addEventListener("click", () => openSlip(id));
  });

  queueList.querySelectorAll("[data-approve]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      const b = items.find((x) => String(x.id) === btn.dataset.approve);
      if (!confirm(`อนุมัติการจอง #${b.id} ยอด ${formatPrice(b.total_price)}?\nตรวจแล้วว่ามีเงินเข้าบัญชีจริง`)) return;
      btn.disabled = true;
      try {
        await AdminAPI.approve(b.id);
        flash(queueList, `อนุมัติ #${b.id} แล้ว ออก e-Ticket ให้ลูกค้าเรียบร้อย`);
        refreshAll();
      } catch (err) {
        btn.disabled = false;
        handleError(err, queueList, true);
      }
    })
  );

  queueList.querySelectorAll("[data-reject]").forEach((btn) =>
    btn.addEventListener("click", () => openReject(items.find((x) => String(x.id) === btn.dataset.reject)))
  );
}

/* ---------------- all bookings ---------------- */
async function loadAll() {
  try {
    const items = await AdminAPI.list(statusFilter.value);
    if (!items.length) {
      allTable.innerHTML = `<tbody><tr><td class="empty-state">ไม่มีรายการ</td></tr></tbody>`;
      return;
    }
    allTable.innerHTML = `
      <thead><tr>
        <th>#</th><th>รายการ / โซน</th><th>ยอด</th><th>ผู้ซื้อ</th><th>สถานะ</th><th>ตรวจโดย</th><th>ตั๋ว / เข้างาน</th><th></th>
      </tr></thead>
      <tbody>
        ${items
          .map(
            (b) => `<tr>
            <td>${esc(b.id)}<div class="muted small">${esc(b.created_at || "")}</div></td>
            <td>${esc(b.race_name)}<div class="muted small">${esc(b.zone_name)} × ${b.quantity}</div></td>
            <td>${formatPrice(b.total_price)}</td>
            <td>${esc(b.buyer_name || "-")}<div class="muted small">${esc(b.buyer_phone || "")} ${b.username ? "• " + esc(b.username) : ""}</div></td>
            <td>${statusBadge(b.status, b.status_label)}${b.reject_reason ? `<div class="muted small">${esc(b.reject_reason)}</div>` : ""}</td>
            <td>${esc(b.reviewed_by || "-")}<div class="muted small">${esc(b.reviewed_at || "")}</div></td>
            <td>${esc(b.ticket_code || "-")}<div class="muted small">${b.checked_in_at ? "เข้างาน " + esc(b.checked_in_at) : ""}</div></td>
            <td class="nowrap">
              ${b.slip_uploaded ? `<button type="button" class="btn btn-link btn-sm" data-view-slip="${esc(b.id)}">ดูสลิป</button>` : ""}
              ${["pending", "awaiting_payment", "rejected", "pending_review"].includes(b.status)
                ? `<button type="button" class="btn btn-link btn-sm danger" data-admin-cancel="${esc(b.id)}">ยกเลิก</button>` : ""}
            </td>
          </tr>`
          )
          .join("")}
      </tbody>`;

    allTable.querySelectorAll("[data-view-slip]").forEach((btn) =>
      btn.addEventListener("click", () => openSlip(btn.dataset.viewSlip))
    );
    allTable.querySelectorAll("[data-admin-cancel]").forEach((btn) =>
      btn.addEventListener("click", async () => {
        if (!confirm(`ยกเลิกการจอง #${btn.dataset.adminCancel} และคืนที่นั่ง?`)) return;
        try {
          await AdminAPI.cancel(btn.dataset.adminCancel);
          refreshAll();
        } catch (err) {
          handleError(err, allTable.parentElement, true);
        }
      })
    );
  } catch (err) {
    handleError(err, allTable.parentElement);
  }
}

/* ---------------- modals ---------------- */
async function openSlip(id) {
  try {
    slipModalImg.src = await slipUrl(id);
    slipModal.hidden = false;
  } catch (err) {
    alert(err.message);
  }
}
document.getElementById("slip-modal-close").addEventListener("click", () => (slipModal.hidden = true));
slipModal.addEventListener("click", (e) => {
  if (e.target === slipModal) slipModal.hidden = true;
});

function openReject(b) {
  rejectTarget = b;
  document.getElementById("reject-title").textContent = `#${b.id} (${formatPrice(b.total_price)})`;
  rejectReason.selectedIndex = b.duplicate_of && b.duplicate_of.length ? 3 : 0;
  rejectOther.hidden = true;
  rejectOther.value = "";
  rejectError.innerHTML = "";
  rejectForm.querySelector('input[value="reupload"]').checked = true;
  rejectModal.hidden = false;
}

rejectReason.addEventListener("change", () => {
  rejectOther.hidden = rejectReason.value !== "__other";
  if (!rejectOther.hidden) rejectOther.focus();
});
document.getElementById("reject-cancel").addEventListener("click", () => (rejectModal.hidden = true));

rejectForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const reason = rejectReason.value === "__other" ? rejectOther.value.trim() : rejectReason.value;
  if (reason.length < 2) {
    showError(rejectError, "กรุณาระบุเหตุผล");
    return;
  }
  const allowReupload = rejectForm.querySelector('input[name="reject-mode"]:checked').value === "reupload";
  const submit = document.getElementById("reject-submit");
  submit.disabled = true;
  try {
    await AdminAPI.reject(rejectTarget.id, reason, allowReupload);
    rejectModal.hidden = true;
    flash(queueList, `ปฏิเสธ #${rejectTarget.id} แล้ว${allowReupload ? " (ลูกค้าแนบใหม่ได้ภายใน 30 นาที)" : " และคืนที่นั่งแล้ว"}`, "warning");
    refreshAll();
  } catch (err) {
    showError(rejectError, err.message);
  } finally {
    submit.disabled = false;
  }
});

/* ---------------- tabs & refresh ---------------- */
document.querySelectorAll(".tabs-bar .tab").forEach((tab) =>
  tab.addEventListener("click", () => {
    activeTab = tab.dataset.tab;
    document.querySelectorAll(".tabs-bar .tab").forEach((t2) => t2.classList.toggle("active", t2 === tab));
    document.querySelectorAll(".tab-panel").forEach((p) => (p.hidden = p.id !== `tab-${activeTab}`));
    refreshAll();
  })
);
statusFilter.addEventListener("change", loadAll);
document.getElementById("refresh-btn").addEventListener("click", () => refreshAll());

function handleError(err, container, flashOnly = false) {
  if (err.status === 401 || err.status === 403) {
    showGuard(err.status === 401 ? "กรุณาเข้าสู่ระบบด้วยบัญชีแอดมิน" : "บัญชีนี้ไม่มีสิทธิ์แอดมิน");
    return;
  }
  if (flashOnly) flash(container, err.message, "error");
  else showError(container, err.message);
}

function showGuard(message) {
  clearInterval(refreshTimer);
  appEl.hidden = true;
  guardEl.innerHTML = `
    <div class="state-card closed">
      <div class="state-icon">🔒</div>
      <h1>${esc(message)}</h1>
      <p>ตั้งสิทธิ์แอดมินด้วยคำสั่ง <code>docker compose exec web python -m app.make_admin &lt;username&gt;</code> แล้วล็อกอินใหม่</p>
      <a class="btn btn-primary" href="${loginUrl()}">เข้าสู่ระบบ</a>
    </div>`;
}

async function refreshAll() {
  try {
    renderSummary(await AdminAPI.summary());
  } catch (err) {
    handleError(err, warningsEl);
    return;
  }
  if (activeTab === "queue") await loadQueue();
  if (activeTab === "all") await loadAll();
}

async function init() {
  if (!getToken()) {
    showGuard("กรุณาเข้าสู่ระบบด้วยบัญชีแอดมิน");
    return;
  }
  try {
    renderSummary(await AdminAPI.summary());
  } catch (err) {
    handleError(err, guardEl);
    return;
  }
  appEl.hidden = false;
  await loadQueue();
  refreshTimer = setInterval(() => {
    if (!modalOpen() && !document.hidden) refreshAll();
  }, REFRESH_MS);
}

init();
