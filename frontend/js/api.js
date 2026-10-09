/* ==========================================================
   api.js
   ฟังก์ชันกลางสำหรับเรียก FastAPI backend ด้วย fetch()
   แนบ JWT (Authorization: Bearer ...) ให้อัตโนมัติถ้าล็อกอินอยู่
   ========================================================== */

const API_BASE = ""; // ใช้ path สัมพัทธ์ เพราะ frontend ถูก serve จาก FastAPI ตัวเดียวกัน

async function apiRequest(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = localStorage.getItem("token");
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = `เกิดข้อผิดพลาด (HTTP ${res.status})`;
    try {
      const data = await res.json();
      if (data.detail) detail = data.detail;
    } catch (e) {
      /* ไม่มี JSON body ก็ใช้ข้อความ default ไป */
    }
    if (res.status === 401) {
      // token หมดอายุ/ไม่ถูกต้อง -> ล้างสถานะล็อกอินเก่า
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

const RaceAPI = {
  listRaces(keyword) {
    const query = keyword ? `?keyword=${encodeURIComponent(keyword)}` : "";
    return apiRequest(`/api/races${query}`);
  },
  getRace(raceId) {
    return apiRequest(`/api/races/${raceId}`);
  },
  getZones(raceId) {
    return apiRequest(`/api/races/${raceId}/zones`);
  },
};

const BookingAPI = {
  create(raceId, zoneId, quantity) {
    return apiRequest(`/api/bookings`, {
      method: "POST",
      body: JSON.stringify({ race_id: raceId, zone_id: zoneId, quantity }),
    });
  },
  get(bookingId) {
    return apiRequest(`/api/bookings/${bookingId}`);
  },
  submitCheckout(bookingId, buyerName, buyerPhone, paymentMethod) {
    return apiRequest(`/api/bookings/${bookingId}/checkout`, {
      method: "POST",
      body: JSON.stringify({
        buyer_name: buyerName,
        buyer_phone: buyerPhone,
        payment_method: paymentMethod,
      }),
    });
  },
  pay(bookingId, paymentMethod) {
    return apiRequest(`/api/bookings/${bookingId}/payment`, {
      method: "POST",
      body: JSON.stringify({ payment_method: paymentMethod }),
    });
  },
  getTicket(bookingId) {
    return apiRequest(`/api/bookings/${bookingId}/ticket`);
  },
};
