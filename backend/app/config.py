"""
config.py
----------
ค่าตั้งค่าที่อ่านจาก environment (.env) รวมไว้ที่เดียว
"""

import os
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# ---- การล็อกที่นั่ง ----
HOLD_MINUTES = _int("HOLD_MINUTES", 10)  # เวลาล็อกที่นั่งก่อนต้องแนบสลิป
REUPLOAD_MINUTES = _int("REUPLOAD_MINUTES", 30)  # เวลาให้แนบสลิปใหม่หลังแอดมินปฏิเสธ

# ---- พร้อมเพย์ของผู้ขาย (ใส่เองใน .env ห้าม commit ค่าจริง) ----
# รับได้: เบอร์มือถือ 10 หลัก (0812345678) / เลขบัตรประชาชน-เลขผู้เสียภาษี 13 หลัก / e-Wallet ID 15 หลัก
PROMPTPAY_ID = os.getenv("PROMPTPAY_ID", "").strip()
PROMPTPAY_NAME = os.getenv("PROMPTPAY_NAME", "").strip()  # ชื่อบัญชีที่แสดงให้ลูกค้าเห็น เช่น "ภูวิศ พ."

# ---- ไฟล์สลิป ----
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", Path(__file__).resolve().parent.parent / "uploads"))
MAX_SLIP_BYTES = _int("MAX_SLIP_MB", 5) * 1024 * 1024

# ---- ระบบตรวจสลิปอัตโนมัติ (ไม่บังคับ) ----
# none     = แอดมินตรวจเองทั้งหมด (ค่าเริ่มต้น)
# easyslip = ส่งสลิปไปตรวจที่ EasySlip ก่อน ผ่านแล้วออกตั๋วทันที ไม่ผ่าน/ระบบล่ม -> เข้าคิวแอดมิน
SLIP_VERIFY_PROVIDER = os.getenv("SLIP_VERIFY_PROVIDER", "none").strip().lower()
SLIP_VERIFY_API_KEY = os.getenv("SLIP_VERIFY_API_KEY", "").strip()
SLIP_VERIFY_URL = os.getenv("SLIP_VERIFY_URL", "https://developer.easyslip.com/api/v1/verify").strip()
# ตัวอักษรบางส่วนของชื่อ/เลขบัญชีผู้รับ ที่ต้องเจอในผลตรวจ (เว้นว่าง = ไม่เช็กผู้รับ)
SLIP_RECEIVER_HINT = os.getenv("SLIP_RECEIVER_HINT", "").strip()
