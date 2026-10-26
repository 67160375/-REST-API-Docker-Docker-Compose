# 🏁 Grid Pass Thailand

เว็บไซต์ระบบจองตั๋วชมการแข่งขันรถ (ภาษาไทย) พัฒนาโดยยึดตาม User Journey
ที่ออกแบบไว้ 6 ขั้นตอน: ค้นหารายการแข่ง → ดูรายละเอียด → เลือกโซนที่นั่ง →
กรอกข้อมูลผู้เข้าชม → ชำระเงิน → รับ e-Ticket

รายละเอียด journey เต็ม ดูที่ [`docs/user-journey.md`](docs/user-journey.md)
รายการ API ทั้งหมด ดูที่ [`docs/api-spec.md`](docs/api-spec.md)

## ฟีเจอร์

- **ตารางการแข่ง** (`/pages/schedule.html`) — แต่ละวันแข่งช่วงเวลาไหน มีรถประเภทอะไร กรองตามประเภทรถได้
- **เลือกโซนจากผังสนาม** — แตะอัฒจันทร์บนภาพเพื่อเลือกโซน สีบอกความหนาแน่น (ว่างเยอะ / ใกล้เต็ม / เต็ม)
- **ล็อกที่นั่ง 10 นาที** พร้อมนับเวลาถอยหลัง หมดเวลาระบบคืนที่นั่งอัตโนมัติ (กันจองชนด้วย `SELECT ... FOR UPDATE`)
- **ชำระด้วย QR พร้อมเพย์ของร้าน** — QR ฝังยอดเงินของแต่ละการจองไว้แล้ว + บันทึกรูป QR ไปเปิดในแอปธนาคารได้
- **แนบสลิป → แอดมินตรวจ → ออก e-Ticket** — หน้าแอดมินมีคิวรอตรวจ ดูสลิป อนุมัติ/ปฏิเสธ เตือนสลิปซ้ำ
- **ตรวจสลิปอัตโนมัติ (ไม่บังคับ)** — เปิดได้ใน `.env` ผ่านก็ออกตั๋วทันที ไม่ผ่านค่อยเข้าคิวแอดมิน
- **ตั๋วของฉัน** — ดูทุกการจองและ QR เข้างานได้ตลอด
- **สแกนตั๋วหน้างาน** (`/pages/scan.html`) — ใช้กล้องมือถือสแกน QR, กันสแกนซ้ำ, เตือนตั๋วผิดวัน

## Tech Stack

| ชั้นระบบ | เทคโนโลยี |
| --- | --- |
| Frontend | HTML + CSS + JavaScript ธรรมดา (ไม่มี framework) |
| Backend | FastAPI (Python) |
| ฐานข้อมูล | PostgreSQL (รันผ่าน Docker Compose) |
| ORM | SQLModel |
| งานเบื้องหลัง | APScheduler (คืนที่นั่งที่หมดเวลาทุก 1 นาที) |
| QR | `frontend/js/vendor/qrcode-generator.js` (สร้าง QR) · `frontend/js/vendor/jsQR.js` (อ่าน QR ตอนสแกน) — ไฟล์อยู่ในโปรเจกต์ ไม่ต้องโหลดจาก CDN |
| การรันระบบ | Docker + Docker Compose |

## โครงสร้างโปรเจกต์

```
Grid-Pass-TH/
├── backend/
│   ├── app/
│   │   ├── main.py           # จุดเริ่มแอป, auto-migration, scheduler, mount frontend
│   │   ├── config.py         # ค่าตั้งค่าจาก .env (พร้อมเพย์, เวลาล็อก, ตรวจสลิป)
│   │   ├── models.py         # ตาราง: User, Race, ScheduleItem, Zone, Booking, Ticket
│   │   ├── schemas.py        # รูปแบบข้อมูลรับ-ส่ง API
│   │   ├── crud.py           # อ่าน/เขียน DB + กติกาการจอง (ล็อกแถว กันจองชน)
│   │   ├── presenters.py     # แปลงข้อมูล DB -> response
│   │   ├── promptpay.py      # สร้างข้อความ QR พร้อมเพย์ (EMVCo) ฝังยอดเงิน
│   │   ├── slip_verify.py    # ตรวจสลิปอัตโนมัติ (ไม่บังคับ)
│   │   ├── seed.py           # ข้อมูลตัวอย่าง: รายการแข่ง โซน ตารางเวลา ตำแหน่งโซนบนผังสนาม
│   │   ├── make_admin.py     # คำสั่งตั้งสิทธิ์ admin / staff
│   │   ├── security.py       # bcrypt + JWT + ตรวจสิทธิ์
│   │   └── routers/          # races, bookings, admin, checkin, auth, users, dev
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── pages/
│   │   ├── races.html            # 1. ค้นหารายการแข่ง
│   │   ├── race-detail.html      # 2. รายละเอียด + ตารางเวลา + ผังสนาม
│   │   ├── schedule.html         #    ตารางการแข่งทุกวัน
│   │   ├── select-zone.html      # 3. เลือกโซนจากผังสนาม & จำนวนตั๋ว
│   │   ├── checkout.html         # 4. กรอกข้อมูลผู้เข้าชม
│   │   ├── payment.html          # 5. QR พร้อมเพย์ + แนบสลิป
│   │   ├── ticket-success.html   # 6. รอตรวจ / e-Ticket + QR เข้างาน
│   │   ├── my-tickets.html       #    ตั๋วของฉัน
│   │   ├── admin.html            #    แอดมินตรวจสลิป
│   │   ├── scan.html             #    สแกนตั๋วหน้างาน
│   │   └── auth.html             #    เข้าสู่ระบบ / สมัครสมาชิก
│   ├── css/style.css
│   ├── js/                   # api.js, common.js + สคริปต์ต่อหน้า + vendor/
│   └── assets/circuit-map.svg  # ภาพผังสนาม "ชั่วคราว"
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md
```

## วิธีรันระบบ (Development)

ต้องมี [Docker](https://www.docker.com/) และ Docker Compose ติดตั้งไว้ก่อน

```bash
# 1) คัดลอกไฟล์ environment ตัวอย่าง (ถ้ามี .env อยู่แล้ว ให้เพิ่มเฉพาะบรรทัดที่ขาด)
cp .env.example .env

# 2) แก้ .env: ใส่ SECRET_KEY และเลขพร้อมเพย์ (PROMPTPAY_ID, PROMPTPAY_NAME)

# 3) รันทั้งระบบ (ครั้งแรกหลังอัปเดตโค้ด ให้ใส่ --build)
docker compose up --build

# 4) เปิดเว็บที่
#    http://localhost:8000              -> หน้าเว็บ
#    http://localhost:8000/docs         -> Swagger UI ทดสอบ API
#    http://localhost:8080              -> Adminer ดู/แก้ข้อมูลใน DB

# ปิดระบบ
docker compose down
```

ตอนเริ่มระบบ backend จะเพิ่มตาราง/คอลัมน์ใหม่ให้ฐานข้อมูลเดิมเอง (ข้อมูลเดิมไม่หาย)
และรวมโซนที่นั่งที่เคยถูกสร้างซ้ำจากบั๊ก seed เดิมให้อัตโนมัติ

### ตั้งแอดมินคนแรก

สมัครสมาชิกผ่านหน้าเว็บก่อน แล้วรัน:

```bash
docker compose exec web python -m app.make_admin <username>          # แอดมิน (ตรวจสลิป + สแกนตั๋ว)
docker compose exec web python -m app.make_admin <username> staff    # พนักงานสแกนตั๋วหน้างาน
```

แล้วออกจากระบบ/ล็อกอินใหม่ เมนู "แอดมิน" และ "สแกนตั๋ว" จะขึ้นที่แถบด้านบน

### Flow การชำระเงิน

1. ลูกค้าเลือกโซน → ระบบล็อกที่นั่ง 10 นาที
2. กรอกชื่อ-เบอร์ → หน้า QR พร้อมเพย์ (ฝังยอดเงินแล้ว) → โอน → แนบสลิป
3. สถานะเป็น "รอตรวจสอบ" (หยุดนับเวลา กันที่นั่งไว้)
4. แอดมินเปิด `/pages/admin.html` เทียบสลิปกับเงินเข้าในแอปธนาคาร → **อนุมัติ** = ออก e-Ticket ทันที
   / **ปฏิเสธ** = ให้แนบใหม่ภายใน 30 นาที หรือยกเลิกคืนที่นั่ง
5. ลูกค้าเห็น e-Ticket ที่หน้าเดิม (เช็กสถานะเองทุก 10 วินาที) หรือที่ "ตั๋วของฉัน"
6. วันงาน พนักงานเปิด `/pages/scan.html` สแกน QR (กล้องต้องเปิดผ่าน https หรือ localhost)

### ตรวจสลิปอัตโนมัติ (ไม่บังคับ)

ตั้งใน `.env`: `SLIP_VERIFY_PROVIDER=easyslip` และ `SLIP_VERIFY_API_KEY=...`
(สมัครกับผู้ให้บริการเอง มีค่าใช้จ่าย) ระบบจะเช็กยอดเงิน เวลาโอน เลขอ้างอิงซ้ำ และผู้รับ (ถ้าตั้ง `SLIP_RECEIVER_HINT`)
ผ่านครบ = ออกตั๋วทันที ไม่ผ่านหรือ API ล่ม = เข้าคิวแอดมินตามปกติ (ระบบจะไม่ปฏิเสธลูกค้าเอง)

> ⚠️ ตัวเชื่อม EasySlip เขียนตามรูปแบบ API ที่เผยแพร่ แต่ยังไม่ได้ทดสอบกับบัญชีจริง
> ก่อนใช้จริงให้ทดสอบด้วยการโอนยอดเล็กๆ แล้วดูผลในหน้าแอดมิน (ข้อความ 🤖)

### เปลี่ยนเป็นข้อมูลจริง (ตารางเวลา / ภาพผังสนาม)

- **ภาพผังสนาม**: วางไฟล์ภาพใน `frontend/assets/` แล้วแก้ `venue_map_url` ของรายการแข่ง (ใน Adminer หรือ `DEFAULT_MAP_URL` ใน `seed.py`)
- **ตำแหน่งโซนบนภาพ**: เปิด `select-zone.html?id=1&mapdebug=1` คลิกมุมซ้ายบนและขวาล่างของอัฒจันทร์บนภาพ
  ระบบจะบอกค่า `map_x, map_y, map_w, map_h` ให้นำไปใส่ในตาราง `zone` (หรือ `ZONE_MAP_POSITIONS` ใน `seed.py`)
- **ตารางเวลา**: แก้ในตาราง `scheduleitem` ผ่าน Adminer หรือแก้ `_SCHEDULE_*` ใน `seed.py`
  (seed เติมให้เฉพาะรายการที่ยังไม่มีตารางเลย ถ้าจะใส่ใหม่ทั้งหมดให้ลบแถวเดิมของรายการนั้นก่อน)

## รันโดยไม่ใช้ Docker (ทางเลือกสำหรับ dev เร็วๆ)

ต้องมี PostgreSQL รันในเครื่อง แล้วตั้งค่า environment ก่อน (ดูตัวอย่างใน `backend/.env.example`)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://appuser:apppassword@localhost:5432/appdb
export SECRET_KEY=$(openssl rand -hex 32)
uvicorn app.main:app --reload --app-dir .
```

จากนั้นเปิด `http://localhost:8000`

### Windows PowerShell — ปัญหาที่มักเจอ

- **`running scripts is disabled on this system`** ตอน activate venv — รันครั้งเดียวก่อน activate:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .venv\Scripts\activate
  ```
  (อนุญาตแค่ terminal หน้าต่างปัจจุบันเท่านั้น ปิดแล้วต้องรันใหม่)

- **ตั้ง environment ใน PowerShell** ใช้ `$env:DATABASE_URL="postgresql://..."` แทน `export`

- **`psycopg2-binary` ติดตั้งไม่ผ่าน (`pg_config executable not found`)** — มักเกิดกับ Python
  เวอร์ชันใหม่มากที่ยังไม่มี wheel สำเร็จรูป ใช้ Python 3.11 หรือรันผ่าน Docker แทน

## แผนงานต่อไป

1. เปลี่ยนตารางเวลาและภาพผังสนามเป็นข้อมูลจริง (รอข้อมูล)
2. แจ้งเตือนแอดมินเมื่อมีสลิปใหม่ (เช่น LINE Messaging API / อีเมล)
3. เปิดตรวจสลิปอัตโนมัติด้วยบริการจริง (ทดสอบด้วยการโอนจริง)
4. ระบบคืนเงิน/ยกเลิกหลังชำระแล้ว
5. Deploy ขึ้น Render/Railway ผ่าน Dockerfile เดียวกับที่ใช้ตอน dev

## Deploy

FastAPI mount โฟลเดอร์ `frontend/` เป็น static files ในตัวเดียวกับ API จึง deploy เป็น container
เดียวได้ทั้งหน้าเว็บและ backend — แนะนำบริการที่รองรับ Docker โดยตรง เช่น Render (ประเภท "Docker")
หรือ Railway โดยให้อ่าน `backend/Dockerfile`

ข้อควรระวังตอน deploy:
- ตั้ง environment ครบตาม `.env.example` (โดยเฉพาะ `SECRET_KEY`, `DATABASE_URL`, `PROMPTPAY_ID`)
- รูปสลิปเก็บที่ `UPLOAD_DIR` (`/app/uploads`) ต้องผูก persistent disk/volume ไม่งั้นรูปหายตอน redeploy
- ปิด/ลบ router `dev` (`/api/dev/reset`) ก่อนใช้งานจริง
- หน้าสแกนตั๋วใช้กล้องได้เฉพาะเว็บที่เป็น https
