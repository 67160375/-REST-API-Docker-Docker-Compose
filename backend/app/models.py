"""
models.py
----------
โครงสร้างตาราง (Entity) ในฐานข้อมูล ออกแบบจากระบบจองตั๋วชมการแข่งขันรถ
รองรับทั้ง Race, Zone, Booking, Ticket และ User (ระบบสมาชิก)
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """ตารางผู้ใช้งานระบบ (ลูกค้า / Admin)"""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    role: str = Field(default="customer")


class Race(SQLModel, table=True):
    """รายการแข่งขัน เช่น Thailand Super Series, BRIC Superbike"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str  # ประเภทการแข่งขัน เช่น "รถยนต์", "มอเตอร์ไซค์"
    race_date: str  # วันที่จัดงาน (รูปแบบ dd/mm/yyyy)
    venue: str  # สนามแข่ง
    price_from: int  # ราคาเริ่มต้น (บาท)
    description: Optional[str] = None
    image_url: Optional[str] = None

    zones: List["Zone"] = Relationship(back_populates="race")
    bookings: List["Booking"] = Relationship(back_populates="race")


class Zone(SQLModel, table=True):
    """โซนที่นั่งของแต่ละรายการแข่งขัน เช่น Grandstand / Side Stand / VIP"""

    id: Optional[int] = Field(default=None, primary_key=True)
    race_id: int = Field(foreign_key="race.id")
    name: str
    price: int
    total_seats: int
    available_seats: int

    race: Optional[Race] = Relationship(back_populates="zones")
    bookings: List["Booking"] = Relationship(back_populates="zone")


class Booking(SQLModel, table=True):
    """การจอง/สั่งซื้อตั๋วของผู้เข้าชม 1 รายการ"""

    id: Optional[int] = Field(default=None, primary_key=True)
    race_id: int = Field(foreign_key="race.id")
    zone_id: int = Field(foreign_key="zone.id")
    quantity: int
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    payment_method: Optional[str] = None  # "promptpay" | "credit_card"
    total_price: int = 0
    status: str = "pending"  # pending -> awaiting_payment -> paid -> cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)

    race: Optional[Race] = Relationship(back_populates="bookings")
    zone: Optional[Zone] = Relationship(back_populates="bookings") # <-- จุดที่แก้ไขแล้ว
    ticket: Optional["Ticket"] = Relationship(back_populates="booking")


class Ticket(SQLModel, table=True):
    """e-Ticket ที่ออกให้หลังชำระเงินสำเร็จ"""

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="booking.id")
    ticket_code: str
    qr_code_data: str
    issued_at: datetime = Field(default_factory=datetime.utcnow)

    booking: Optional[Booking] = Relationship(back_populates="ticket")