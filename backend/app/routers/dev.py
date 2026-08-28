"""
routers/dev.py -- endpoint สำหรับ dev/ทดสอบเท่านั้น ไม่ควรเปิดใช้ตอน deploy จริง
"""
from fastapi import APIRouter
from app import crud

router = APIRouter(prefix="/api/dev", tags=["dev-only"])


@router.post("/reset")
def reset_data():
    """รีเซ็ตที่นั่งคงเหลือกลับเป็นค่าตั้งต้น + ล้างการจอง/ตั๋วทั้งหมด"""
    crud.reset_all_data()
    return {"status": "success", "message": "รีเซ็ตข้อมูลที่นั่งและการจองทั้งหมดแล้ว"}