"""
routers/dev.py -- endpoint สำหรับ dev/ทดสอบเท่านั้น ไม่ควรเปิดใช้ตอน deploy จริง
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import crud
from app.database import get_db
from app.models import User
from app.security import require_admin

router = APIRouter(prefix="/api/dev", tags=["dev-only"])


@router.post("/reset")
def reset_data(_admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """รีเซ็ตที่นั่งคงเหลือกลับเป็นค่าตั้งต้น + ล้างการจอง/ตั๋วทั้งหมด (เฉพาะ admin)"""
    crud.reset_all_data(db)
    return {"status": "success", "message": "รีเซ็ตข้อมูลที่นั่งและการจองทั้งหมดแล้ว"}
