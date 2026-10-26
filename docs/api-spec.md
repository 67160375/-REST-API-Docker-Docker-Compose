# API Spec — Grid Pass Thailand

Base URL (dev): `http://localhost:8000`
เอกสาร Swagger (ทดสอบ API ได้จริง): `http://localhost:8000/docs`

ทุก endpoint อ่าน/เขียน PostgreSQL จริง ส่วนที่ต้องล็อกอินให้ส่ง header
`Authorization: Bearer <access_token>` (ได้จาก `/api/v1/auth/login`)

สิทธิ์ผู้ใช้ (role): `customer` (ค่าเริ่มต้น) · `staff` (สแกนตั๋วหน้างาน) · `admin` (ตรวจสลิป + ทุกอย่าง)

## Races & Schedule (ไม่ต้องล็อกอิน)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/races` | รายการแข่งขันทั้งหมด รองรับ `?keyword=` ค้นหาชื่อ/ประเภท |
| GET | `/api/races/{race_id}` | รายละเอียด + `schedule` (ตารางเวลาในวันแข่ง) + `venue_map_url` (ภาพผังสนาม) |
| GET | `/api/races/{race_id}/schedule` | ตารางเวลาของรายการนี้ |
| GET | `/api/races/{race_id}/zones` | โซนที่นั่ง + ที่นั่งคงเหลือ + `crowd_level` + ตำแหน่งบนภาพผังสนาม (`map_x/y/w/h` หน่วย %) |
| GET | `/api/schedule` | ตารางการแข่งทุกรายการ เรียงตามวันที่ (1 รายการ = 1 วัน) |

## Bookings (ต้องล็อกอิน เห็นเฉพาะของตัวเอง)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| POST | `/api/bookings` | ล็อกที่นั่งชั่วคราว 10 นาที (body: `race_id`, `zone_id`, `quantity` 1-10) |
| GET | `/api/bookings/mine` | การจองทั้งหมดของฉัน |
| GET | `/api/bookings/{id}` | สถานะการจอง (มี `seconds_left` = เวลาที่เหลือ คำนวณฝั่ง server) |
| POST | `/api/bookings/{id}/checkout` | บันทึกชื่อ + เบอร์โทรผู้ซื้อ (`buyer_name`, `buyer_phone`) |
| GET | `/api/bookings/{id}/payment-info` | ยอดเงิน + `promptpay_payload` (ข้อความ QR พร้อมเพย์ที่ฝังยอดแล้ว) |
| POST | `/api/bookings/{id}/slip` | แนบสลิป (multipart field `file`: JPG/PNG/WEBP ≤ 5MB) → `pending_review` |
| GET | `/api/bookings/{id}/ticket` | e-Ticket + `qr_code_data` (เฉพาะสถานะ `paid`) |
| POST | `/api/bookings/{id}/cancel` | ยกเลิก + คืนที่นั่ง (ได้ก่อนส่งสลิปเท่านั้น) |

### สถานะการจอง

```
pending ──checkout──▶ awaiting_payment ──แนบสลิป──▶ pending_review ──อนุมัติ──▶ paid ──สแกน──▶ (checked_in_at)
   │                        │                            │
   └──── หมดเวลา ───────────┴──▶ expired                  ├──ปฏิเสธ (ให้แนบใหม่ 30 นาที)──▶ rejected ──แนบใหม่──▶ pending_review
                                                          └──ปฏิเสธ + ยกเลิก──▶ cancelled (คืนที่นั่ง)
```

- `pending` / `awaiting_payment` / `rejected` มีเวลาจำกัด (`expires_at`) หมดเวลาแล้วระบบคืนที่นั่งอัตโนมัติ (APScheduler ทุก 1 นาที)
- `pending_review` หยุดนับเวลา กันที่นั่งไว้จนแอดมินตัดสิน

## Admin (role `admin`)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/admin/summary` | จำนวนแต่ละสถานะ ยอดขายที่อนุมัติแล้ว ที่นั่งแต่ละโซน |
| GET | `/api/admin/bookings?status=pending_review` | รายการจอง (ค่าเริ่มต้น = คิวรอตรวจ เก่าสุดก่อน, `status=` ว่าง = ทั้งหมด) มี `duplicate_of` = การจองอื่นที่ใช้รูปสลิปเดียวกัน |
| GET | `/api/admin/bookings/{id}` | รายละเอียด 1 รายการ |
| GET | `/api/admin/bookings/{id}/slip` | ไฟล์รูปสลิป |
| POST | `/api/admin/bookings/{id}/approve` | อนุมัติ → ออก e-Ticket (เรียกซ้ำได้ ไม่ออกตั๋วซ้ำ) |
| POST | `/api/admin/bookings/{id}/reject` | ปฏิเสธ body: `reason`, `allow_reupload` (true = ให้แนบใหม่, false = ยกเลิก+คืนที่นั่ง) |
| POST | `/api/admin/bookings/{id}/cancel` | ยกเลิกการจองที่ยังไม่จ่าย + คืนที่นั่ง |

## Check-in (role `staff` หรือ `admin`)

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| POST | `/api/checkin` | body: `code` (ข้อความใน QR หรือ `TIX-000123`), `force` |

ผลลัพธ์ `result`: `ok` · `already_used` · `not_found` · `not_paid` · `wrong_day`
(`wrong_day` = วันนี้ไม่ใช่วันแข่ง ยังไม่บันทึก ต้องส่ง `force: true` เพื่อยืนยันให้เข้า)

## Auth & Users

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | สมัครสมาชิก |
| POST | `/api/v1/auth/login` | เข้าสู่ระบบ → `access_token` |
| POST | `/api/v1/auth/change-password` | เปลี่ยนรหัสผ่าน |
| GET | `/api/v1/users/me` | ข้อมูลตัวเอง (รวม role) |
| GET/PUT/DELETE | `/api/v1/users/{id}` | เจ้าของบัญชีหรือแอดมิน (เปลี่ยน role ได้เฉพาะแอดมิน) |

## System

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/health` | ตรวจสอบว่า backend รันอยู่ปกติ |
| POST | `/api/dev/reset` | (admin, dev เท่านั้น) ล้างการจอง/ตั๋ว คืนที่นั่งทั้งหมด |
