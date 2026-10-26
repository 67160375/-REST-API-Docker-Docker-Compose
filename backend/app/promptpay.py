"""
promptpay.py
-------------
สร้างข้อความ (payload) สำหรับ QR พร้อมเพย์ ตามมาตรฐาน EMVCo / Thai QR Payment
ฝังยอดเงินไว้ใน QR เลย ลูกค้าสแกนแล้วไม่ต้องพิมพ์ยอดเอง

ฝั่งหน้าเว็บจะนำ payload นี้ไปวาดเป็นรูป QR (frontend/js/vendor/qrcode-generator.js)
"""

import re
from typing import Optional

_AID_PROMPTPAY = "A000000677010111"


def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def crc16_ccitt(data: str) -> str:
    """CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) ตามที่ EMVCo กำหนด"""
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def normalize_id(raw: str) -> Optional[tuple[str, str]]:
    """แปลงเลขพร้อมเพย์เป็น (sub-tag, ค่า) ตามชนิด หรือ None ถ้ารูปแบบไม่ถูก"""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 10 and digits.startswith("0"):  # เบอร์มือถือ -> 0066 + ตัด 0 หน้า
        return "01", "0066" + digits[1:]
    if len(digits) == 13:  # เลขบัตรประชาชน / เลขผู้เสียภาษี
        return "02", digits
    if len(digits) == 15:  # e-Wallet ID
        return "03", digits
    return None


def build_payload(promptpay_id: str, amount: float) -> str:
    """สร้าง payload QR พร้อมเพย์แบบระบุยอดเงิน (dynamic QR)"""
    target = normalize_id(promptpay_id)
    if not target:
        raise ValueError("รูปแบบ PROMPTPAY_ID ไม่ถูกต้อง (ใช้เบอร์ 10 หลัก, เลข 13 หลัก หรือ e-Wallet 15 หลัก)")
    sub_tag, value = target

    merchant = _tlv("00", _AID_PROMPTPAY) + _tlv(sub_tag, value)
    payload = (
        _tlv("00", "01")  # Payload Format Indicator
        + _tlv("01", "12")  # 12 = QR ใช้ครั้งเดียว/ระบุยอด
        + _tlv("29", merchant)
        + _tlv("58", "TH")
        + _tlv("53", "764")  # สกุลเงินบาท
        + _tlv("54", f"{amount:.2f}")
        + "6304"
        # ลำดับ field เหมือนไลบรารี promptpay-qr ที่ใช้กันแพร่หลาย (สแกนผ่านแอปธนาคารไทยได้)
    )
    return payload + crc16_ccitt(payload)
