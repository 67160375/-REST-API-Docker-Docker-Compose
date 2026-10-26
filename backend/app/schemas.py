"""
schemas.py
-----------
รูปแบบข้อมูลรับ-ส่งผ่าน API (Pydantic)
แยกออกจาก models.py (ตารางฐานข้อมูล) เพื่อไม่ให้ field ภายใน DB
(เช่น path ไฟล์สลิป, hash, ข้อความ QR) รั่วไหลออกไปใน response โดยไม่ตั้งใจ
"""

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------- Race ----------

class RaceSummary(BaseModel):
    """ใช้ในหน้ารายการแข่งขัน (/races)"""
    id: int
    name: str
    category: str
    race_date: str
    venue: str
    price_from: int
    image_url: Optional[str] = None


class ScheduleItemOut(BaseModel):
    id: int
    start_time: str
    end_time: Optional[str] = None
    category: str
    session_type: str
    title: str
    note: Optional[str] = None


class RaceDetail(RaceSummary):
    """ใช้ในหน้ารายละเอียดการแข่งขัน (/race-detail)"""
    description: Optional[str] = None
    venue_map_url: Optional[str] = None
    schedule: List[ScheduleItemOut] = []


class RaceSchedule(RaceSummary):
    """ใช้ในหน้าตารางการแข่ง (/schedule)"""
    schedule: List[ScheduleItemOut] = []


# ---------- Zone ----------

class ZoneOut(BaseModel):
    """ใช้ในหน้าเลือกโซน (/select-zone)"""
    id: int
    race_id: int
    name: str
    price: int
    available_seats: int
    total_seats: int
    map_x: Optional[float] = None
    map_y: Optional[float] = None
    map_w: Optional[float] = None
    map_h: Optional[float] = None
    description: Optional[str] = None  # จุดเด่นของโซน (คั่นบรรทัดด้วย \n)

    # Stand Crowd Status — คำนวณอัตโนมัติจาก available_seats / total_seats
    crowd_level: Optional[str] = None   # "low" | "medium" | "full"
    crowd_label: Optional[str] = None   # ข้อความภาษาไทยสำหรับแสดงผล เช่น "ว่างเยอะ"

    @model_validator(mode="after")
    def compute_crowd_status(self):
        """
        เกณฑ์การแบ่งสถานะความหนาแน่นของ Stand:
          - ที่นั่งเหลือ = 0                -> เต็ม
          - เหลือ < 50% ของทั้งหมด        -> ใกล้เต็ม
          - เหลือ >= 50%                  -> ว่างเยอะ
        """
        ratio = (self.available_seats / self.total_seats) if self.total_seats > 0 else 0
        if self.available_seats <= 0:
            self.crowd_level, self.crowd_label = "full", "เต็ม"
        elif ratio < 0.5:
            self.crowd_level, self.crowd_label = "medium", "ใกล้เต็ม"
        else:
            self.crowd_level, self.crowd_label = "low", "ว่างเยอะ"
        return self


# ---------- Booking ----------

class BookingCreate(BaseModel):
    """ผู้ใช้เลือกโซน + จำนวนตั๋ว แล้วกด 'ล็อกที่นั่งชั่วคราว'"""
    race_id: int
    zone_id: int
    quantity: int = Field(ge=1, le=10)


class BookingOut(BaseModel):
    id: int
    race_id: int
    zone_id: int
    race_name: str = "-"
    race_date: str = "-"
    zone_name: str = "-"
    quantity: int
    total_price: int
    status: str
    status_label: str = ""
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    payment_method: Optional[str] = None
    seconds_left: Optional[int] = None  # เวลาที่เหลือก่อนหมดสิทธิ์ (วินาที) คำนวณฝั่ง server
    slip_uploaded: bool = False
    reject_reason: Optional[str] = None
    has_ticket: bool = False


class CheckoutInfo(BaseModel):
    """ข้อมูลจากหน้ากรอกข้อมูลผู้เข้าชม (/checkout)"""
    buyer_name: str = Field(min_length=2, max_length=100)
    buyer_phone: str
    payment_method: str = "promptpay"  # ตอนนี้รองรับพร้อมเพย์อย่างเดียว

    @field_validator("buyer_name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("กรุณากรอกชื่อ-นามสกุล")
        return v

    @field_validator("buyer_phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = re.sub(r"[\s-]", "", v)
        if not re.fullmatch(r"0\d{9}", v):
            raise ValueError("เบอร์โทรต้องขึ้นต้นด้วย 0 และมี 10 หลัก")
        return v


class PaymentInfo(BaseModel):
    """ข้อมูลหน้าชำระเงิน: QR พร้อมเพย์ที่ฝังยอดเงินไว้แล้ว"""
    booking: BookingOut
    amount: int
    promptpay_payload: Optional[str] = None  # ข้อความสำหรับวาด QR (None = ยังไม่ได้ตั้งค่า)
    promptpay_name: Optional[str] = None
    promptpay_masked_id: Optional[str] = None  # เช่น xxx-xxx-5678
    config_error: Optional[str] = None


class TicketOut(BaseModel):
    """ใช้ในหน้ารับ e-Ticket (/ticket-success)"""
    booking_id: int
    ticket_code: str
    qr_code_data: str
    race_name: str
    zone_name: str
    quantity: int
    buyer_name: str
    venue: str
    race_date: str
    checked_in_at: Optional[str] = None


# ---------- Admin ----------

class RejectRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=200)
    allow_reupload: bool = True


class AdminBookingOut(BookingOut):
    username: Optional[str] = None
    created_at: Optional[str] = None
    slip_uploaded_at: Optional[str] = None
    duplicate_of: List[int] = []  # การจองอื่นที่ใช้สลิปไฟล์เดียวกัน
    verify_note: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    ticket_code: Optional[str] = None
    checked_in_at: Optional[str] = None


# ---------- Check-in ----------

class CheckInRequest(BaseModel):
    code: str = Field(min_length=3, max_length=200)
    force: bool = False  # ยืนยันให้เข้างานแม้วันที่ไม่ตรง


class CheckInResult(BaseModel):
    result: str  # ok | already_used | not_found | not_paid | wrong_day
    message: str
    ticket_code: Optional[str] = None
    race_name: Optional[str] = None
    race_date: Optional[str] = None
    zone_name: Optional[str] = None
    quantity: Optional[int] = None
    buyer_name: Optional[str] = None
    checked_in_at: Optional[str] = None
    date_warning: Optional[str] = None
