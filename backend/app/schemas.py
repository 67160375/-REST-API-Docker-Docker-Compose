"""
schemas.py
-----------
รูปแบบข้อมูลรับ-ส่งผ่าน API (Pydantic)
แยกออกจาก models.py (ตารางฐานข้อมูล) ตามคำแนะนำใน workshop
เพื่อไม่ให้ field ภายใน DB รั่วไหลออกไปใน response โดยไม่ตั้งใจ
"""

from typing import Optional, List
from pydantic import BaseModel


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


class ActivityItem(BaseModel):
    time: str
    title: str


class RaceDetail(RaceSummary):
    """ใช้ในหน้ารายละเอียดการแข่งขัน (/race-detail)"""
    description: Optional[str] = None
    venue_map_url: Optional[str] = None
    activities: List[ActivityItem] = []


# ---------- Zone ----------

class ZoneOut(BaseModel):
    """ใช้ในหน้าเลือกโซน (/select-zone)"""
    id: int
    race_id: int
    name: str
    price: int
    available_seats: int
    total_seats: int


# ---------- Booking ----------

class BookingCreate(BaseModel):
    """ผู้ใช้เลือกโซน + จำนวนตั๋ว แล้วกด 'ล็อกที่นั่งชั่วคราว'"""
    race_id: int
    zone_id: int
    quantity: int


class BookingOut(BaseModel):
    id: int
    race_id: int
    zone_id: int
    quantity: int
    total_price: int
    status: str
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    payment_method: Optional[str] = None


class CheckoutInfo(BaseModel):
    """ข้อมูลจากหน้ากรอกข้อมูลผู้เข้าชม (/checkout)"""
    buyer_name: str
    buyer_phone: str
    payment_method: str  # "promptpay" | "credit_card"


class PaymentRequest(BaseModel):
    """ข้อมูลจากหน้าชำระเงิน (/payment) — รอบนี้เป็น mock payment เท่านั้น"""
    payment_method: str


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
