"""
models.py
----------
โครงสร้างตาราง (Entity) ในฐานข้อมูล ออกแบบจากระบบจองตั๋วชมการแข่งขันรถ
รองรับ Race, ScheduleItem, Zone, Booking, Ticket และ User (ระบบสมาชิก)

หมายเหตุ: ตารางที่มีอยู่แล้วใน DB จะไม่ถูกเพิ่มคอลัมน์ใหม่โดย create_all
คอลัมน์ใหม่ทุกตัวจึงต้องอยู่ใน COLUMN_MIGRATIONS ของ main.py ด้วย
"""

from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """ตารางผู้ใช้งานระบบ (customer / staff / admin)"""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)  # bcrypt hash (user เก่าจะถูก hash ตอนล็อกอินครั้งแรก)
    role: str = Field(default="customer")  # customer | staff (สแกนตั๋วหน้างาน) | admin


class Race(SQLModel, table=True):
    """รายการแข่งขัน 1 รายการ = จัด 1 วัน เช่น Thailand Super Series, BRIC Superbike"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str  # ประเภทการแข่งขัน เช่น "รถยนต์", "มอเตอร์ไซค์"
    race_date: str  # วันที่จัดงาน (รูปแบบ dd/mm/yyyy)
    venue: str  # สนามแข่ง
    price_from: int  # ราคาเริ่มต้น (บาท)
    description: Optional[str] = None
    image_url: Optional[str] = None
    venue_map_url: Optional[str] = None  # ภาพผังสนาม/จุดชม ที่ใช้ในหน้าเลือกโซน

    zones: List["Zone"] = Relationship(back_populates="race")
    bookings: List["Booking"] = Relationship(back_populates="race")
    schedule: List["ScheduleItem"] = Relationship(back_populates="race")


class ScheduleItem(SQLModel, table=True):
    """ตารางเวลาในวันแข่ง: ช่วงเวลา + ประเภทรถ/รุ่น + ชื่อรายการ"""

    id: Optional[int] = Field(default=None, primary_key=True)
    race_id: int = Field(foreign_key="race.id", index=True)
    start_time: str  # "HH:MM" (24 ชม.) เรียงลำดับด้วย string ได้เลย
    end_time: Optional[str] = None  # "HH:MM"
    category: str  # ประเภทรถ/รุ่น เช่น "Super Car GT3", "Superbike 1000cc", "กิจกรรม"
    session_type: str = "race"  # practice | qualifying | race | activity
    title: str
    note: Optional[str] = None

    race: Optional[Race] = Relationship(back_populates="schedule")


class Zone(SQLModel, table=True):
    """โซนที่นั่งของแต่ละรายการแข่งขัน เช่น Grandstand / Side Stand / VIP"""

    id: Optional[int] = Field(default=None, primary_key=True)
    race_id: int = Field(foreign_key="race.id")
    name: str
    price: int
    total_seats: int
    available_seats: int

    # ตำแหน่งจุดกดบนภาพผังสนาม หน่วยเป็น % ของความกว้าง/สูงภาพ (0-100)
    # ไม่ใส่ = ไม่แสดงจุดบนภาพ (ยังเลือกจากรายการด้านล่างได้)
    map_x: Optional[float] = None
    map_y: Optional[float] = None
    map_w: Optional[float] = None
    map_h: Optional[float] = None

    race: Optional[Race] = Relationship(back_populates="zones")
    bookings: List["Booking"] = Relationship(back_populates="zone")


class Booking(SQLModel, table=True):
    """
    การจอง/สั่งซื้อตั๋วของผู้เข้าชม 1 รายการ

    สถานะ:
      pending          ล็อกที่นั่งแล้ว (มีเวลาจำกัด expires_at)
      awaiting_payment กรอกข้อมูลผู้ซื้อแล้ว รอโอน + แนบสลิป (ยังนับเวลาอยู่)
      pending_review   แนบสลิปแล้ว รอแอดมินตรวจ (หยุดนับเวลา กันที่นั่งไว้)
      rejected         แอดมินปฏิเสธสลิป ให้แนบใหม่ภายในเวลา expires_at
      paid             อนุมัติแล้ว ออก e-Ticket
      cancelled        ยกเลิก (คืนที่นั่งแล้ว)
      expired          หมดเวลา (คืนที่นั่งแล้ว)
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)  # เจ้าของการจอง
    race_id: int = Field(foreign_key="race.id")
    zone_id: int = Field(foreign_key="zone.id")
    quantity: int
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    payment_method: Optional[str] = None  # "promptpay"
    total_price: int = 0
    status: str = "pending"
    expires_at: Optional[datetime] = Field(default=None)  # UTC (naive)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # ---- สลิปโอนเงิน ----
    slip_path: Optional[str] = None  # ชื่อไฟล์ใน UPLOAD_DIR (ไม่เปิดเป็น public)
    slip_hash: Optional[str] = Field(default=None, index=True)  # sha256 ของไฟล์ ใช้จับสลิปซ้ำ
    slip_uploaded_at: Optional[datetime] = None
    slip_ref: Optional[str] = Field(default=None, index=True)  # เลขอ้างอิงจาก API ตรวจสลิป (ถ้าใช้)
    verify_note: Optional[str] = None  # ผลจากระบบตรวจสลิปอัตโนมัติ (ถ้าเปิดใช้)

    # ---- ผลการตรวจของแอดมิน ----
    reviewed_by: Optional[int] = Field(default=None, foreign_key="user.id")
    reviewed_at: Optional[datetime] = None
    reject_reason: Optional[str] = None

    race: Optional[Race] = Relationship(back_populates="bookings")
    zone: Optional[Zone] = Relationship(back_populates="bookings")
    ticket: Optional["Ticket"] = Relationship(back_populates="booking")


class Ticket(SQLModel, table=True):
    """e-Ticket ที่ออกให้หลังแอดมินอนุมัติการชำระเงิน (1 booking = 1 ticket ใช้ได้ quantity คน)"""

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="booking.id")
    ticket_code: str
    qr_code_data: str  # ข้อความใน QR: "GRIDPASS:<token สุ่ม>" เดาไม่ได้
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    checked_in_at: Optional[datetime] = None
    checked_in_by: Optional[int] = Field(default=None, foreign_key="user.id")

    booking: Optional[Booking] = Relationship(back_populates="ticket")
