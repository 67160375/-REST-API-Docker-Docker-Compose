"""
main.py
--------
จุดเริ่มต้นของ backend (FastAPI)
- สร้างตารางทั้งหมดลง PostgreSQL อัตโนมัติ
- mount โฟลเดอร์ frontend/ เป็น static files (เว็บหน้าบ้าน)
- เปิด API routes ใต้ /api/*
- เปิด Swagger UI อัตโนมัติที่ /docs
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.database import engine
from app import models
from app.routers import races, bookings, auth, users, dev

app = FastAPI(
    title="Grid Pass API",
    description="API สำหรับระบบจองตั๋วชมการแข่งขันรถ",
    version="0.1.0",
)

# เปิด CORS ไว้กว้างๆ ก่อนในช่วง dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# สั่งสร้างตารางทั้งหมด (รวมถึงตาราง users) ใน PostgreSQL ทันทีตอนเซิร์ฟเวอร์เริ่มรัน
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


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