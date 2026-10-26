"""
main.py
--------
จุดเริ่มต้นของ backend (FastAPI)
- สร้างตาราง + เพิ่มคอลัมน์/index ใหม่ให้ DB เดิมอัตโนมัติ (auto-migration แบบง่าย)
- ใส่/อัปเดตข้อมูลตัวอย่าง
- ตั้งระบบ APScheduler คืนที่นั่งของการจองที่หมดเวลาอัตโนมัติทุก 1 นาที
- mount โฟลเดอร์ frontend/ เป็น static files (เว็บหน้าบ้าน)
- เปิด API routes ใต้ /api/* และ Swagger UI ที่ /docs
"""

from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlmodel import Session, SQLModel, select

from app import config, crud, models  # noqa: F401  (models ต้อง import ก่อน create_all)
from app.database import engine
from app.models import User
from app.routers import admin, auth, bookings, checkin, dev, races, users
from app.seed import seed_if_empty, sync_sample_data


def auto_release_expired_bookings():
    """Background Job: คืนที่นั่งของการจองที่หมดเวลา (ทำงานทุก 1 นาที)"""
    try:
        with Session(engine) as db:
            released = crud.release_expired_bookings(db)
            if released:
                print(f"[APScheduler] Released {released} expired booking(s).")
    except Exception as e:  # noqa: BLE001 - อย่าให้ job ตายเพราะ error ครั้งเดียว
        print(f"[APScheduler] release job error: {e}")


scheduler = BackgroundScheduler()
scheduler.add_job(auto_release_expired_bookings, "interval", minutes=1)


# create_all สร้างได้แค่ "ตารางใหม่" ไม่เพิ่มคอลัมน์ให้ตารางที่มีอยู่แล้ว
# คอลัมน์ที่เพิ่มทีหลังทุกตัวต้องอยู่ในลิสต์นี้ (IF NOT EXISTS จึงรันซ้ำได้ปลอดภัย)
COLUMN_MIGRATIONS = [
    ("booking", "user_id", "INTEGER"),
    ("booking", "slip_path", "VARCHAR"),
    ("booking", "slip_hash", "VARCHAR"),
    ("booking", "slip_uploaded_at", "TIMESTAMP WITHOUT TIME ZONE"),
    ("booking", "slip_ref", "VARCHAR"),
    ("booking", "verify_note", "VARCHAR"),
    ("booking", "reviewed_by", "INTEGER"),
    ("booking", "reviewed_at", "TIMESTAMP WITHOUT TIME ZONE"),
    ("booking", "reject_reason", "VARCHAR"),
    ("race", "venue_map_url", "VARCHAR"),
    ("zone", "map_x", "DOUBLE PRECISION"),
    ("zone", "map_y", "DOUBLE PRECISION"),
    ("zone", "map_w", "DOUBLE PRECISION"),
    ("zone", "map_h", "DOUBLE PRECISION"),
    ("zone", "description", "VARCHAR"),
    ("ticket", "checked_in_at", "TIMESTAMP WITHOUT TIME ZONE"),
    ("ticket", "checked_in_by", "INTEGER"),
]

# Index เพิ่มประสิทธิภาพ query
#  - idx_booking_open_expires : งานคืนที่นั่งที่หมดเวลา (รันทุก 1 นาที)
#  - idx_booking_review_queue : คิวรอตรวจสลิปของแอดมิน
#  - idx_zone_race_id         : หน้าเลือกโซน
#  - uq_ticket_booking_id     : 1 booking มี 1 ticket (กันออกตั๋วซ้ำ)
#  - uq_ticket_qr             : หา ticket จากข้อความใน QR ตอนสแกนเข้างาน
INDEX_STATEMENTS = [
    "DROP INDEX IF EXISTS idx_booking_open_expires",
    """CREATE INDEX IF NOT EXISTS idx_booking_open_expires_v2
       ON booking (expires_at)
       WHERE status IN ('pending', 'awaiting_payment', 'rejected')""",
    """CREATE INDEX IF NOT EXISTS idx_booking_review_queue
       ON booking (slip_uploaded_at)
       WHERE status = 'pending_review'""",
    "CREATE INDEX IF NOT EXISTS idx_booking_slip_hash ON booking (slip_hash)",
    "CREATE INDEX IF NOT EXISTS idx_booking_slip_ref ON booking (slip_ref)",
    "CREATE INDEX IF NOT EXISTS idx_zone_race_id ON zone (race_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_booking_id ON ticket (booking_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_qr ON ticket (qr_code_data)",
]


def run_migrations() -> None:
    statements = [
        f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS {column} {col_type}'
        for table, column, col_type in COLUMN_MIGRATIONS
    ] + INDEX_STATEMENTS
    failed = 0
    for stmt in statements:
        try:  # แยกทีละคำสั่ง อันไหนพังจะไม่ลากอันอื่นพังไปด้วย
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"[System] Migration note: {' '.join(stmt.split())[:80]} -> {e.__class__.__name__}: {e}")
    print(f"[System] Auto-migration done ({len(statements) - failed}/{len(statements)} ok).")


def promote_admins_from_env() -> None:
    """ตั้ง role admin ให้ชื่อผู้ใช้ใน ADMIN_USERNAMES (เฉพาะคนที่สมัครไว้แล้ว)"""
    if not config.ADMIN_USERNAMES:
        return
    with Session(engine) as db:
        users = db.exec(select(User).where(User.username.in_(config.ADMIN_USERNAMES))).all()
        for user in users:
            if user.role != "admin":
                user.role = "admin"
                db.add(user)
                print(f"[System] Promoted '{user.username}' to admin (ADMIN_USERNAMES).")
        db.commit()
        missing = set(config.ADMIN_USERNAMES) - {u.username for u in users}
        if missing:
            print(f"[System] ADMIN_USERNAMES not registered yet: {', '.join(sorted(missing))}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    run_migrations()
    seed_if_empty()
    sync_sample_data()
    promote_admins_from_env()
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    scheduler.start()
    print("[System] Database ready & APScheduler started.")
    yield
    scheduler.shutdown()
    print("[System] APScheduler stopped.")


app = FastAPI(
    title="Grid Pass API",
    description="API สำหรับระบบจองตั๋วชมการแข่งขันรถ",
    version="0.2.0",
    lifespan=lifespan,
)

# เปิด CORS ไว้กว้างๆ ก่อนในช่วง dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def revalidate_frontend_files(request, call_next):
    """ให้เบราว์เซอร์เช็กไฟล์หน้าเว็บ (js/css/html) ใหม่ทุกครั้ง กันค้างเวอร์ชันเก่าหลังอัปเดต
    (ไฟล์ไม่เปลี่ยน = ได้ 304 กลับมา ไม่ต้องโหลดซ้ำ จึงไม่ช้าลง)"""
    response = await call_next(request)
    if not request.url.path.startswith("/api"):
        response.headers.setdefault("Cache-Control", "no-cache")
    return response


app.include_router(races.router)
app.include_router(bookings.router)
app.include_router(admin.router)
app.include_router(checkin.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dev.router)


@app.get("/api/health")
def health_check():
    """ใช้เช็คว่า backend รันอยู่ปกติ"""
    return {"status": "ok", "service": "grid-pass-api"}


# หา path ของโฟลเดอร์ frontend
_THIS_DIR = Path(__file__).resolve().parent
_CANDIDATE_DIRS = [
    _THIS_DIR.parent / "frontend",
    _THIS_DIR.parent.parent / "frontend",
]
FRONTEND_DIR = next((p for p in _CANDIDATE_DIRS if p.is_dir()), _CANDIDATE_DIRS[0])

# mount frontend เป็น static files ไว้ท้ายสุด (ไม่งั้นจะทับ /api)
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
