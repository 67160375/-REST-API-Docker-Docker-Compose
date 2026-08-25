# API Spec — Race Ticket Thailand

Base URL (dev): `http://localhost:8000`
เอกสาร Swagger (ทดสอบ API ได้จริง): `http://localhost:8000/docs`

รอบนี้ (สัปดาห์ 1) ทุก endpoint คืนค่าจาก **mock data** ใน `backend/app/crud.py`
ยังไม่เชื่อมฐานข้อมูล PostgreSQL จริง — โครงสร้างตั้งชื่อ/รูปแบบ response ให้
ตรงกับที่จะใช้จริงในสัปดาห์ที่ 2 แล้ว

## Races

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/races` | รายการแข่งขันทั้งหมด รองรับ query `?keyword=` ค้นหาชื่อ/ประเภท |
| GET | `/api/races/{race_id}` | รายละเอียดการแข่งขัน 1 รายการ (รวมกำหนดการกิจกรรม) |
| GET | `/api/races/{race_id}/zones` | โซนที่นั่งทั้งหมดของรายการแข่งขันนี้ พร้อมที่นั่งคงเหลือ |

## Bookings

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| POST | `/api/bookings` | สร้างการจอง/ล็อกที่นั่งชั่วคราว (body: `race_id`, `zone_id`, `quantity`) |
| GET | `/api/bookings/{booking_id}` | ดูสรุปการจองปัจจุบัน |
| POST | `/api/bookings/{booking_id}/checkout` | บันทึกข้อมูลผู้ซื้อ + ช่องทางชำระเงิน |
| POST | `/api/bookings/{booking_id}/payment` | ประมวลผลการชำระเงิน (mock) แล้วออก e-Ticket |
| GET | `/api/bookings/{booking_id}/ticket` | เรียกดู e-Ticket ที่ออกแล้ว |

## System

| Method | Path | คำอธิบาย |
| --- | --- | --- |
| GET | `/api/health` | ตรวจสอบว่า backend รันอยู่ปกติ |

## สิ่งที่ต้องทำต่อ (สัปดาห์ 2 เป็นต้นไป)

- เชื่อม `database.py` + `models.py` เข้ากับ endpoint จริง แทนที่ mock data ใน `crud.py`
- เพิ่มการตรวจสอบสิทธิ์ (authorization) ในจุดที่แก้ไข/ยกเลิกการจอง
- เพิ่ม endpoint สำหรับยกเลิกการจอง/ขอคืนเงิน
- เพิ่มกลไกปล่อยที่นั่งคืนอัตโนมัติเมื่อผู้ใช้ไม่ชำระเงินภายในเวลาที่กำหนด
