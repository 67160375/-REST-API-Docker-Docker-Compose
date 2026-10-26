/* ==========================================================
   api.js
   ฟังก์ชันกลางสำหรับเรียก FastAPI backend ด้วย fetch()
   แนบ JWT (Authorization: Bearer ...) ให้อัตโนมัติถ้าล็อกอินอยู่
   ========================================================== */

const API_BASE = ""; // ใช้ path สัมพัทธ์ เพราะ frontend ถูก serve จาก FastAPI ตัวเดียวกัน

// แปลง error ของ FastAPI ให้เป็นข้อความอ่านง่าย (422 จะส่ง detail มาเป็น list)
function _errorDetail(data, status) {
  if (!data || data.detail === undefined) return `เกิดข้อผิดพลาด (HTTP ${status})`;
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((d) => String(d.msg || "").replace(/^Value error,\s*/i, ""))
      .filter(Boolean)
      .join(" / ") || "ข้อมูลไม่ถูกต้อง";
  }
  return `เกิดข้อผิดพลาด (HTTP ${status})`;
}

async function apiRequest(path, options = {}) {
  const isForm = options.body instanceof FormData;
  const headers = { ...(isForm ? {} : { "Content-Type": "application/json" }), ...(options.headers || {}) };
  const token = localStorage.getItem("token");
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (e) {
    const err = new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ กรุณาตรวจสอบอินเทอร์เน็ตแล้วลองใหม่");
    err.status = 0;
    throw err;
  }

  if (!res.ok) {
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      /* ไม่มี JSON body ก็ใช้ข้อความ default ไป */
    }
    if (res.status === 401) {
      // token หมดอายุ/ไม่ถูกต้อง -> ล้างสถานะล็อกอินเก่า
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
    const err = new Error(_errorDetail(data, res.status));
    err.status = res.status;
    throw err;
  }

  const type = res.headers.get("content-type") || "";
  return type.includes("application/json") ? res.json() : res.blob();
}

const RaceAPI = {
  listRaces(keyword) {
    const query = keyword ? `?keyword=${encodeURIComponent(keyword)}` : "";
    return apiRequest(`/api/races${query}`);
  },
  getRace(raceId) {
    return apiRequest(`/api/races/${encodeURIComponent(raceId)}`);
  },
  getZones(raceId) {
    return apiRequest(`/api/races/${encodeURIComponent(raceId)}/zones`);
  },
  allSchedules() {
    return apiRequest(`/api/schedule`);
  },
};

const BookingAPI = {
  create(raceId, zoneId, quantity) {
    return apiRequest(`/api/bookings`, {
      method: "POST",
      body: JSON.stringify({ race_id: raceId, zone_id: zoneId, quantity }),
    });
  },
  mine() {
    return apiRequest(`/api/bookings/mine`);
  },
  get(bookingId) {
    return apiRequest(`/api/bookings/${encodeURIComponent(bookingId)}`);
  },
  submitCheckout(bookingId, buyerName, buyerPhone) {
    return apiRequest(`/api/bookings/${encodeURIComponent(bookingId)}/checkout`, {
      method: "POST",
      body: JSON.stringify({ buyer_name: buyerName, buyer_phone: buyerPhone, payment_method: "promptpay" }),
    });
  },
  paymentInfo(bookingId) {
    return apiRequest(`/api/bookings/${encodeURIComponent(bookingId)}/payment-info`);
  },
  uploadSlip(bookingId, file) {
    const form = new FormData();
    form.append("file", file);
    return apiRequest(`/api/bookings/${encodeURIComponent(bookingId)}/slip`, { method: "POST", body: form });
  },
  getTicket(bookingId) {
    return apiRequest(`/api/bookings/${encodeURIComponent(bookingId)}/ticket`);
  },
  cancel(bookingId) {
    return apiRequest(`/api/bookings/${encodeURIComponent(bookingId)}/cancel`, { method: "POST" });
  },
};

const AdminAPI = {
  summary() {
    return apiRequest(`/api/admin/summary`);
  },
  list(status) {
    return apiRequest(`/api/admin/bookings?status=${encodeURIComponent(status || "")}`);
  },
  slip(bookingId) {
    return apiRequest(`/api/admin/bookings/${encodeURIComponent(bookingId)}/slip`); // คืนเป็น Blob
  },
  approve(bookingId) {
    return apiRequest(`/api/admin/bookings/${encodeURIComponent(bookingId)}/approve`, { method: "POST" });
  },
  reject(bookingId, reason, allowReupload) {
    return apiRequest(`/api/admin/bookings/${encodeURIComponent(bookingId)}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason, allow_reupload: allowReupload }),
    });
  },
  cancel(bookingId) {
    return apiRequest(`/api/admin/bookings/${encodeURIComponent(bookingId)}/cancel`, { method: "POST" });
  },
};

const CheckInAPI = {
  scan(code, force = false) {
    return apiRequest(`/api/checkin`, { method: "POST", body: JSON.stringify({ code, force }) });
  },
};

const UserAPI = {
  me() {
    return apiRequest(`/api/v1/users/me`);
  },
};
