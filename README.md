# 🏁 Grid Pass Thailand

เว็บไซต์ระบบจองตั๋วชมการแข่งขันรถ (ภาษาไทย) พัฒนาโดยยึดตาม User Journey
ที่ออกแบบไว้ 6 ขั้นตอน: ค้นหารายการแข่ง → ดูรายละเอียด → เลือกโซนที่นั่ง →
กรอกข้อมูลผู้เข้าชม → ชำระเงิน → รับ e-Ticket

รายละเอียด journey เต็ม ดูที่ [`docs/user-journey.md`](docs/user-journey.md)
รายการ API ทั้งหมด ดูที่ [`docs/api-spec.md`](docs/api-spec.md)

## Tech Stack

| ชั้นระบบ | เทคโนโลยี |
| --- | --- |
| Frontend | HTML + CSS + JavaScript ธรรมดา (ไม่มี framework) |
| Backend | FastAPI (Python) |
| ฐานข้อมูล | PostgreSQL (รันผ่าน Docker Compose — พร้อมใช้ในสัปดาห์ที่ 2) |
| ORM | SQLModel |
| การรันระบบ | Docker + Docker Compose |

รอบนี้ (สัปดาห์ 1 / Kickoff) endpoint ทั้งหมดยังคืนค่าเป็น **mock data**
(ดู `backend/app/crud.py`) ยังไม่ได้เขียน/อ่านจาก PostgreSQL จริง แต่ได้เตรียม
`database.py` และ `models.py` ไว้ให้พร้อมสำหรับต่อยอดในรอบถัดไปแล้ว

## โครงสร้างโปรเจกต์

```
Grid-Pass-thailand/
├── backend/
│   ├── app/
│   │   ├── main.py           # จุดเริ่มแอป, mount static files (frontend) + include routers
│   │   ├── routers/
│   │   │   ├── races.py      # GET /api/races, /api/races/{id}, /api/races/{id}/zones
│   │   │   └── bookings.py   # POST/GET /api/bookings/...
│   │   ├── models.py         # SQLModel: โครงสร้างตาราง (พร้อมใช้สัปดาห์ที่ 2)
│   │   ├── schemas.py        # Pydantic: รูปแบบข้อมูลรับ-ส่งผ่าน API
│   │   ├── database.py       # การเชื่อมต่อฐานข้อมูล PostgreSQL (พร้อมใช้สัปดาห์ที่ 2)
│   │   └── crud.py           # mock data + ฟังก์ชันอ่าน/เขียนข้อมูล (สัปดาห์นี้ยังเป็น in-memory)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html            # redirect ไปหน้ารายการแข่งขัน
│   ├── pages/
│   │   ├── races.html            # 1. ค้นหารายการแข่ง
│   │   ├── race-detail.html      # 2. ดูรายละเอียด & รอบแข่ง
│   │   ├── select-zone.html      # 3. เลือกโซน & จำนวนตั๋ว
│   │   ├── checkout.html         # 4. กรอกข้อมูลผู้เข้าชม
│   │   ├── payment.html          # 5. ชำระเงิน
│   │   └── ticket-success.html   # 6. รับ e-Ticket
│   ├── css/style.css
│   ├── js/
│   │   ├── api.js            # fetch() เรียก FastAPI ทุกจุด
│   │   ├── common.js         # header/footer, localStorage state, format ราคา
│   │   └── <page>.js         # ไฟล์สคริปต์ต่อหน้า
│   └── assets/
├── docs/
│   ├── user-journey.md
│   └── api-spec.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## วิธีรันระบบ (Development)

ต้องมี [Docker](https://www.docker.com/) และ Docker Compose ติดตั้งไว้ก่อน

```bash
# 1) คัดลอกไฟล์ environment ตัวอย่าง
cp .env.example .env

# 2) รันทั้งระบบ (backend + frontend + database)
docker compose up

# 3) เปิดเว็บที่
#    http://localhost:8000              -> หน้าเว็บ (frontend)
#    http://localhost:8000/docs         -> Swagger UI ทดสอบ API
#    http://localhost:8000/api/health   -> เช็คว่า backend รันอยู่

# ปิดระบบ
docker compose down
```

แก้โค้ดในเครื่องแล้วเห็นผลทันที เพราะ `docker-compose.yml` mount โฟลเดอร์
`backend/app` และ `frontend` เป็น volume ไว้แล้ว ไม่ต้อง build image ใหม่ทุกครั้ง

## รันโดยไม่ใช้ Docker (ทางเลือกสำหรับ dev เร็วๆ)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

จากนั้นเปิด `http://localhost:8000`

### Windows PowerShell — ปัญหาที่มักเจอ

- **`running scripts is disabled on this system`** ตอน activate venv — เปิด
  PowerShell ปกติ (ไม่ต้อง admin) แล้วรันครั้งเดียวก่อน activate:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .venv\Scripts\activate
  ```
  (คำสั่งนี้อนุญาตแค่ terminal หน้าต่างปัจจุบันเท่านั้น ปิดแล้วต้องรันใหม่)

- **`psycopg2-binary` ติดตั้งไม่ผ่าน (`pg_config executable not found`)** —
  มักเกิดกับ Python เวอร์ชันใหม่มากที่ยังไม่มี wheel สำเร็จรูป ข้ามได้เลยใน
  รอบนี้เพราะยังไม่ได้เชื่อมฐานข้อมูลจริง ติดตั้งเฉพาะที่ใช้งานจริงก่อน:
  ```powershell
  pip install fastapi==0.115.0 "uvicorn[standard]==0.30.6" sqlmodel==0.0.22 python-multipart==0.0.9 pydantic==2.9.2
  ```
  (พอถึงตอนเชื่อม PostgreSQL จริงในสัปดาห์ที่ 2 ค่อยกลับมาแก้ปัญหานี้ หรือใช้
  Docker ซึ่งไม่เจอปัญหานี้เพราะ build บน Linux)

## แผนงานต่อไป (สัปดาห์ 2 เป็นต้นไป)

1. เชื่อม `database.py`/`models.py` เข้ากับ PostgreSQL จริง แทนที่ mock data ใน `crud.py`
2. เพิ่มระบบล็อกที่นั่งแบบมี timeout จริง (กันการจองซ้อน/ race condition)
3. เพิ่มระบบล็อกอิน/สิทธิ์ผู้ใช้ (ถ้าต้องการ)
4. เชื่อมผู้ให้บริการชำระเงินจริง แทน mock payment
5. Deploy ขึ้น Render/Railway ผ่าน Dockerfile เดียวกับที่ใช้ตอน dev

## Deploy

เพราะ FastAPI mount โฟลเดอร์ `frontend/` เป็น static files ในตัวเดียวกับ API
จึง deploy เป็น container เดียวได้ทั้งเว็บหน้าบ้านและ backend — แนะนำใช้บริการที่
รองรับ Docker โดยตรง เช่น Render (ประเภท "Docker" service) หรือ Railway
โดยเชื่อมบัญชี GitHub แล้วให้บริการอ่าน `backend/Dockerfile` แล้ว build/deploy
อัตโนมัติทุกครั้งที่ push เข้า branch `main`
