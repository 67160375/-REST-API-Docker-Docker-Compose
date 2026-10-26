"""
crud.py
--------
จัดการการอ่าน-เขียนข้อมูลกับ PostgreSQL ผ่าน SQLModel / SQLAlchemy Session
- ล็อกแถวด้วย with_for_update() ทุกจุดที่เปลี่ยนที่นั่ง/สถานะ กันการจองชนกันและกดซ้ำ
- คืนที่นั่งอัตโนมัติเมื่อการจองหมดเวลา

ฟังก์ชันที่ผิดเงื่อนไขทางธุรกิจจะ raise BookingError(ข้อความภาษาไทย, http_status)
ให้ router แปลงเป็น HTTPException อีกที
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, col, delete, select

from app import config
from app.models import Booking, Race, ScheduleItem, Ticket, User, Zone

OPEN_STATUSES = ("pending", "awaiting_payment", "rejected")  # ยังมีเวลาจำกัด (expires_at)
HELD_STATUSES = OPEN_STATUSES + ("pending_review",)  # ยังกันที่นั่งไว้อยู่ แต่ยังไม่จ่าย


class BookingError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def utcnow() -> datetime:
    return datetime.utcnow()


def as_utc_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """ระบบเก็บเวลาเป็น UTC แบบไม่มี timezone ถ้า DB คืนค่าแบบมี timezone มา ก็แปลงให้เหมือนกัน"""
    if dt is not None and dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def is_expired(booking: Booking) -> bool:
    expires_at = as_utc_naive(booking.expires_at)
    return booking.status in OPEN_STATUSES and expires_at is not None and expires_at <= utcnow()


def seconds_left(booking: Booking) -> Optional[int]:
    expires_at = as_utc_naive(booking.expires_at)
    if booking.status not in OPEN_STATUSES or expires_at is None:
        return None
    return max(0, int((expires_at - utcnow()).total_seconds()))


# ---------------------------------------------------------------
# Race / Schedule / Zone
# ---------------------------------------------------------------
def list_races(db: Session, keyword: Optional[str] = None) -> List[Race]:
    statement = select(Race).order_by(Race.id)
    if keyword:
        kw = f"%{keyword.strip().lower()}%"
        statement = statement.where(
            (col(Race.name).ilike(kw)) | (col(Race.category).ilike(kw))
        )
    return db.exec(statement).all()


def get_race(db: Session, race_id: int) -> Optional[Race]:
    return db.get(Race, race_id)


def list_schedule(db: Session, race_id: int) -> List[ScheduleItem]:
    statement = (
        select(ScheduleItem)
        .where(ScheduleItem.race_id == race_id)
        .order_by(ScheduleItem.start_time, ScheduleItem.id)
    )
    return db.exec(statement).all()


def list_zones(db: Session, race_id: int) -> List[Zone]:
    statement = select(Zone).where(Zone.race_id == race_id).order_by(Zone.price, Zone.id)
    return db.exec(statement).all()


def get_zone(db: Session, zone_id: int) -> Optional[Zone]:
    return db.get(Zone, zone_id)


# ---------------------------------------------------------------
# Booking
# ---------------------------------------------------------------
def _lock_booking(db: Session, booking_id: int) -> Optional[Booking]:
    """SELECT ... FOR UPDATE + โหลดค่าล่าสุดจาก DB ทับของเดิมใน session"""
    statement = (
        select(Booking)
        .where(Booking.id == booking_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return db.exec(statement).first()


def _release_seats(db: Session, booking: Booking) -> None:
    statement = (
        select(Zone)
        .where(Zone.id == booking.zone_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    zone = db.exec(statement).first()
    if zone:
        zone.available_seats = min(zone.total_seats, zone.available_seats + booking.quantity)
        db.add(zone)


def _expire_now(db: Session, booking: Booking) -> None:
    """ใช้ตอนพบว่าหมดเวลาก่อน scheduler จะมาเก็บ: คืนที่นั่งทันที (ล็อกแถวก่อน กันคืนซ้ำ)"""
    locked = _lock_booking(db, booking.id)
    if locked and is_expired(locked):
        _release_seats(db, locked)
        locked.status = "expired"
        db.add(locked)
    db.commit()


def create_booking(db: Session, user_id: int, race_id: int, zone_id: int, quantity: int) -> Booking:
    statement = (
        select(Zone).where(Zone.id == zone_id).with_for_update().execution_options(populate_existing=True)
    )
    zone = db.exec(statement).first()
    if not zone or zone.race_id != race_id:
        raise BookingError("ไม่พบโซนนี้ในรายการแข่งขันที่เลือก", 404)
    if quantity < 1 or quantity > 10:
        raise BookingError("จองได้ครั้งละ 1-10 ใบ")
    if zone.available_seats < quantity:
        raise BookingError("ที่นั่งในโซนนี้ไม่พอ กรุณาเลือกโซนอื่นหรือลดจำนวน")

    zone.available_seats -= quantity
    db.add(zone)

    booking = Booking(
        user_id=user_id,
        race_id=race_id,
        zone_id=zone_id,
        quantity=quantity,
        total_price=zone.price * quantity,
        status="pending",
        expires_at=utcnow() + timedelta(minutes=config.HOLD_MINUTES),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking(db: Session, booking_id: int) -> Optional[Booking]:
    return db.get(Booking, booking_id)


def list_user_bookings(db: Session, user_id: int) -> List[Booking]:
    statement = select(Booking).where(Booking.user_id == user_id).order_by(col(Booking.id).desc())
    return db.exec(statement).all()


def update_checkout_info(db: Session, booking_id: int, buyer_name: str, buyer_phone: str) -> Booking:
    booking = _lock_booking(db, booking_id)
    if not booking:
        raise BookingError("ไม่พบการจองนี้", 404)
    if is_expired(booking):
        _expire_now(db, booking)
        raise BookingError("หมดเวลาล็อกที่นั่งแล้ว กรุณาจองใหม่", 410)
    if booking.status not in ("pending", "awaiting_payment"):
        raise BookingError("การจองนี้แก้ไขข้อมูลผู้ซื้อไม่ได้แล้ว")

    booking.buyer_name = buyer_name
    booking.buyer_phone = buyer_phone
    booking.payment_method = "promptpay"
    booking.status = "awaiting_payment"
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def find_slip_duplicates(db: Session, slip_hash: str, exclude_booking_id: int) -> List[int]:
    statement = select(Booking.id).where(
        Booking.slip_hash == slip_hash, Booking.id != exclude_booking_id
    )
    return list(db.exec(statement).all())


def slip_ref_used(db: Session, ref: str, exclude_booking_id: int) -> bool:
    statement = select(Booking.id).where(Booking.slip_ref == ref, Booking.id != exclude_booking_id)
    return db.exec(statement).first() is not None


def assert_can_attach_slip(db: Session, booking: Booking) -> None:
    """เช็กว่าการจองนี้แนบสลิปได้ไหม (ถ้าหมดเวลาแล้วจะคืนที่นั่งให้ทันที)"""
    if is_expired(booking):
        _expire_now(db, booking)
        raise BookingError("หมดเวลาชำระเงินแล้ว ที่นั่งถูกคืนเข้าระบบ กรุณาจองใหม่", 410)
    if booking.status == "pending":
        raise BookingError("กรุณากรอกข้อมูลผู้ซื้อก่อนชำระเงิน")
    if booking.status not in ("awaiting_payment", "rejected"):
        raise BookingError("การจองนี้แนบสลิปไม่ได้ (อาจส่งสลิปไปแล้วหรือถูกยกเลิก)")


def attach_slip(db: Session, booking_id: int, slip_path: str, slip_hash: str) -> Booking:
    """บันทึกสลิป -> สถานะ pending_review (หยุดนับเวลา กันที่นั่งไว้จนแอดมินตัดสิน)"""
    booking = _lock_booking(db, booking_id)
    if not booking:
        raise BookingError("ไม่พบการจองนี้", 404)
    assert_can_attach_slip(db, booking)

    booking.slip_path = slip_path
    booking.slip_hash = slip_hash
    booking.slip_uploaded_at = utcnow()
    booking.slip_ref = None
    booking.verify_note = None
    booking.reject_reason = None
    booking.status = "pending_review"
    booking.expires_at = None
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def set_verify_result(db: Session, booking_id: int, note: str, ref: Optional[str]) -> None:
    booking = _lock_booking(db, booking_id)
    if booking:
        booking.verify_note = note
        booking.slip_ref = ref
        db.add(booking)
        db.commit()


def _new_ticket(booking: Booking) -> Ticket:
    return Ticket(
        booking_id=booking.id,
        ticket_code=f"TIX-{booking.id:06d}",
        qr_code_data=f"GRIDPASS:{secrets.token_urlsafe(18)}",
    )


def approve_booking(db: Session, booking_id: int, reviewer_id: Optional[int]) -> Ticket:
    """อนุมัติการชำระเงิน -> ออก e-Ticket (เรียกซ้ำได้ ไม่ออกตั๋วซ้ำ)"""
    booking = _lock_booking(db, booking_id)
    if not booking:
        raise BookingError("ไม่พบการจองนี้", 404)

    existing = get_ticket(db, booking_id)
    if booking.status == "paid" and existing:
        return existing
    if booking.status != "pending_review":
        raise BookingError("อนุมัติได้เฉพาะรายการที่รอตรวจสอบเท่านั้น")

    booking.status = "paid"
    booking.reviewed_by = reviewer_id
    booking.reviewed_at = utcnow()
    booking.reject_reason = None
    db.add(booking)

    ticket = existing or _new_ticket(booking)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def reject_booking(
    db: Session, booking_id: int, reviewer_id: int, reason: str, allow_reupload: bool
) -> Booking:
    booking = _lock_booking(db, booking_id)
    if not booking:
        raise BookingError("ไม่พบการจองนี้", 404)
    if booking.status != "pending_review":
        raise BookingError("ปฏิเสธได้เฉพาะรายการที่รอตรวจสอบเท่านั้น")

    booking.reviewed_by = reviewer_id
    booking.reviewed_at = utcnow()
    booking.reject_reason = reason
    if allow_reupload:
        booking.status = "rejected"
        booking.expires_at = utcnow() + timedelta(minutes=config.REUPLOAD_MINUTES)
    else:
        _release_seats(db, booking)
        booking.status = "cancelled"
        booking.expires_at = None
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_ticket(db: Session, booking_id: int) -> Optional[Ticket]:
    return db.exec(select(Ticket).where(Ticket.booking_id == booking_id)).first()


def cancel_booking(db: Session, booking_id: int, by_admin: bool = False) -> Booking:
    """ยกเลิกและคืนที่นั่ง: ลูกค้ายกเลิกได้ก่อนส่งสลิป, แอดมินยกเลิกได้ทุกสถานะที่ยังไม่จ่าย"""
    booking = _lock_booking(db, booking_id)
    if not booking:
        raise BookingError("ไม่พบการจองนี้", 404)
    allowed = HELD_STATUSES if by_admin else OPEN_STATUSES
    if booking.status not in allowed:
        if booking.status == "pending_review":
            raise BookingError("ส่งสลิปแล้ว กำลังรอแอดมินตรวจสอบ ยกเลิกเองไม่ได้ กรุณาติดต่อผู้จัดงาน")
        raise BookingError("ไม่สามารถยกเลิกการจองนี้ได้ (อาจถูกยกเลิกไปแล้ว หมดเวลา หรือชำระเงินเรียบร้อยแล้ว)")

    _release_seats(db, booking)
    booking.status = "cancelled"
    booking.expires_at = None
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


# ---------------------------------------------------------------
# เช็กอินหน้างาน
# ---------------------------------------------------------------
def find_ticket_by_code(db: Session, code: str) -> Optional[Ticket]:
    code = code.strip()
    if code.upper().startswith("TIX-"):
        statement = select(Ticket).where(Ticket.ticket_code == code.upper())
    else:
        statement = select(Ticket).where(Ticket.qr_code_data == code)
    return db.exec(statement.with_for_update().execution_options(populate_existing=True)).first()


def check_in(db: Session, ticket: Ticket, staff_id: int) -> None:
    ticket.checked_in_at = utcnow()
    ticket.checked_in_by = staff_id
    db.add(ticket)
    db.commit()
    db.refresh(ticket)


# ---------------------------------------------------------------
# Admin
# ---------------------------------------------------------------
def admin_list_bookings(db: Session, status: Optional[str], limit: int = 100) -> List[Booking]:
    statement = select(Booking)
    if status:
        statement = statement.where(Booking.status == status)
    if status == "pending_review":
        statement = statement.order_by(Booking.slip_uploaded_at, Booking.id)  # เก่าสุดก่อน
    else:
        statement = statement.order_by(col(Booking.id).desc())
    return db.exec(statement.limit(limit)).all()


def status_counts(db: Session) -> dict:
    rows = db.exec(select(Booking.status, func.count()).group_by(Booking.status)).all()
    return {s: c for s, c in rows}


def paid_revenue(db: Session) -> int:
    total = db.exec(select(func.coalesce(func.sum(Booking.total_price), 0)).where(Booking.status == "paid")).one()
    return int(total or 0)


def sold_seats_by_zone(db: Session) -> dict:
    rows = db.exec(
        select(Booking.zone_id, func.sum(Booking.quantity))
        .where(Booking.status == "paid")
        .group_by(Booking.zone_id)
    ).all()
    return {z: int(q or 0) for z, q in rows}


def get_user(db: Session, user_id: Optional[int]) -> Optional[User]:
    return db.get(User, user_id) if user_id else None


# ---------------------------------------------------------------
# Background Job & Dev Utilities
# ---------------------------------------------------------------
def release_expired_bookings(db: Session) -> int:
    """คืนที่นั่งของการจองที่หมดเวลาแล้ว (APScheduler รันทุก 1 นาที)"""
    statement = (
        select(Booking)
        .where(
            col(Booking.status).in_(OPEN_STATUSES),
            col(Booking.expires_at) != None,  # noqa: E711
            col(Booking.expires_at) < utcnow(),
        )
        .with_for_update(skip_locked=True)
    )
    expired = db.exec(statement).all()
    for booking in expired:
        _release_seats(db, booking)
        booking.status = "expired"
        db.add(booking)
    if expired:
        db.commit()
    return len(expired)


def reset_all_data(db: Session) -> None:
    """รีเซ็ตข้อมูลการจองทั้งหมดใน DB (ใช้ตอน Dev/Test)"""
    db.exec(delete(Ticket))
    db.exec(delete(Booking))
    for z in db.exec(select(Zone)).all():
        z.available_seats = z.total_seats
        db.add(z)
    db.commit()
