"""
main.py
--------
จุดเริ่มต้นของ backend (FastAPI)
- สร้างตารางทั้งหมดลง PostgreSQL อัตโนมัติ
- ตั้งระบบ APScheduler คืนตั๋วหมดอายุอัตโนมัติทุก 1 นาที
- mount โฟลเดอร์ frontend/ เป็น static files (เว็บหน้าบ้าน)
- เปิด API routes ใต้ /api/*
- เปิด Swagger UI อัตโนมัติที่ /docs
"""

from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlmodel import Session, SQLModel

from app import crud, models
from app.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE booking ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
        conn.commit()
except Exception as e:
    pass
from app.routers import auth, bookings, dev, races, users
from app.seed import seed_if_empty


# ฟังก์ชัน Background Job คืนตั๋วหลุดจองที่หมดอายุ (ทำงานทุก 1 นาที)
def auto_release_expired_bookings():
    with Session(engine) as db:
        released_count = crud.release_expired_bookings(db)
        if released_count > 0:
            print(f"[APScheduler] Released {released_count} expired booking(s).")


# ตั้งค่า Background Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(auto_release_expired_bookings, "interval", minutes=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: สร้างตารางใน PostgreSQL
    SQLModel.metadata.create_all(engine)
<<<<<<< HEAD
    
    # --- [ส่วนที่เพิ่มใหม่] เพิ่มคอลัมน์ user_id เข้าตาราง booking อัตโนมัติหากยังไม่มี ---
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE booking ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            conn.commit()
            print("[System] Auto-migration: user_id column verified.")
    except Exception as e:
        print(f"[System] Migration note: {e}")
    # -------------------------------------------------------------------------

=======
>>>>>>> f6020754512dbed3d50b11f68de4e438c8d05959
    seed_if_empty()
    scheduler.start()
    print("[System] Database tables verified & APScheduler started.")
    
    yield
    
    # Shutdown: ปิดระบบ Background Job เมื่อปิดเซิร์ฟเวอร์
    scheduler.shutdown()
    print("[System] APScheduler stopped.")


app = FastAPI(
    title="Grid Pass API",
    description="API สำหรับระบบจองตั๋วชมการแข่งขันรถ",
    version="0.1.0",
    lifespan=lifespan,
)

# เปิด CORS ไว้กว้างๆ ก่อนในช่วง dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# รวม router ของแต่ละหมวด
app.include_router(races.router)
app.include_router(bookings.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dev.router)


@app.get("/api/health")
def health_check():
    """ใช้เช็คว่า backend รันอยู่ปกติ"""
    return {"status": "ok", "service": "race-ticket-thailand-api"}


# หา path ของโฟลเดอร์ frontend
_THIS_DIR = Path(__file__).resolve().parent
_CANDIDATE_DIRS = [
    _THIS_DIR.parent / "frontend",
    _THIS_DIR.parent.parent / "frontend",
]
FRONTEND_DIR = next((p for p in _CANDIDATE_DIRS if p.is_dir()), _CANDIDATE_DIRS[0])

# mount frontend เป็น static files ไว้ท้ายสุด
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")