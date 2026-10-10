"""
crud.py
--------
จัดการการอ่าน-เขียนข้อมูลกับ PostgreSQL ผ่าน SQLModel / SQLAlchemy Session
รวมถึง transactional safety (with_for_update) ป้องกันการจองตั๋วชนกัน
และระบบคืนที่นั่งอัตโนมัติเมื่อตั๋วหมดอายุ
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, col, delete, select

from app.models import Booking, Race, Ticket, Zone


# ---------------------------------------------------------------
# Race & Zone Operations
# ---------------------------------------------------------------
def list_races(db: Session, keyword: Optional[str] = None) -> List[Race]:
    statement = select(Race)
    if keyword:
        kw = f"%{keyword.strip().lower()}%"
        statement = statement.where(
            (col(Race.name).ilike(kw)) | (col(Race.category).ilike(kw))
        )
    return db.exec(statement).all()


def get_race(db: Session, race_id: int) -> Optional[Race]:
    return db.get(Race, race_id)


def list_zones(db: Session, race_id: int) -> List[Zone]:
    statement = select(Zone).where(Zone.race_id == race_id)
    return db.exec(statement).all()


def get_zone(db: Session, zone_id: int) -> Optional[Zone]:
    return db.get(Zone, zone_id)


# ---------------------------------------------------------------
# Booking & Ticket Operations
# ---------------------------------------------------------------
def create_booking(db: Session, race_id: int, zone_id: int, quantity: int) -> Optional[Booking]:
    """
    สร้างรายการจองแบบ Transactional Safety:
    ใช้ with_for_update() เพื่อล็อกแถวของ Zone ไม่ให้ถูกตัดที่นั่งพร้อมกัน (Race Condition)
    """
    statement = select(Zone).where(Zone.id == zone_id).with_for_update()
    zone = db.exec(statement).first()

    if not zone or zone.available_seats < quantity:
        return None

    zone.available_seats -= quantity
    db.add(zone)

    # ใช้ UTC naive datetime เพื่อให้สอดคล้องกับ created_at และ PostgreSQL TIMESTAMP WITHOUT TIME ZONE
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    booking = Booking(
        race_id=race_id,
        zone_id=zone_id,
        quantity=quantity,
        total_price=zone.price * quantity,
        status="pending",
        expires_at=expires_at,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking(db: Session, booking_id: int) -> Optional[Booking]:
    return db.get(Booking, booking_id)


def update_checkout_info(
    db: Session, booking_id: int, buyer_name: str, buyer_phone: str, payment_method: str
) -> Optional[Booking]:
    booking = db.get(Booking, booking_id)
    if not booking or booking.status not in ["pending", "awaiting_payment"]:
        return None

    booking.buyer_name = buyer_name
    booking.buyer_phone = buyer_phone
    booking.payment_method = payment_method
    booking.status = "awaiting_payment"

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def confirm_payment(db: Session, booking_id: int, payment_method: str) -> Optional[Ticket]:
    booking = db.get(Booking, booking_id)
    if not booking or booking.status in ["cancelled", "expired", "paid"]:
        return None

    booking.payment_method = payment_method
    booking.status = "paid"
    db.add(booking)

    ticket_code = f"TIX-{booking.id:06d}"
    ticket = Ticket(
        booking_id=booking.id,
        ticket_code=ticket_code,
        qr_code_data=f"race-ticket-thailand://verify/{ticket_code}",
    )
    db.add(ticket)

    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket(db: Session, booking_id: int) -> Optional[Ticket]:
    statement = select(Ticket).where(Ticket.booking_id == booking_id)
    return db.exec(statement).first()


def cancel_booking(db: Session, booking_id: int) -> bool:
    """ยกเลิกการจองและคืนที่นั่งให้ Zone"""
    statement = select(Booking).where(Booking.id == booking_id).with_for_update()
    booking = db.exec(statement).first()

    if not booking or booking.status in ["cancelled", "paid"]:
        return False

    zone = db.exec(select(Zone).where(Zone.id == booking.zone_id).with_for_update()).first()
    if zone:
        zone.available_seats += booking.quantity
        db.add(zone)

    booking.status = "cancelled"
    db.add(booking)
    db.commit()
    return True


# ---------------------------------------------------------------
# Background Job & Dev Utilities
# ---------------------------------------------------------------
def release_expired_bookings(db: Session) -> int:
    """คืนที่นั่งของการจองที่หมดเวลาแล้ว (APScheduler รันทุก 1 นาที)"""
    now = datetime.utcnow()
    statement = (
        select(Booking)
        .where(
            col(Booking.status).in_(["pending", "awaiting_payment"]),
            col(Booking.expires_at) != None,  # noqa: E711
            col(Booking.expires_at) < now,
        )
        .with_for_update()
    )
    expired_bookings = db.exec(statement).all()

    released_count = 0
    for booking in expired_bookings:
        zone = db.exec(select(Zone).where(Zone.id == booking.zone_id).with_for_update()).first()
        if zone:
            zone.available_seats += booking.quantity
            db.add(zone)

        booking.status = "expired"
        db.add(booking)
        released_count += 1

    if released_count > 0:
        db.commit()

    return released_count


def reset_all_data(db: Session):
    """รีเซ็ตข้อมูลการจองทั้งหมดใน DB (ใช้ตอน Dev/Test)"""
    db.exec(delete(Ticket))
    db.exec(delete(Booking))

    zones = db.exec(select(Zone)).all()
    for z in zones:
        z.available_seats = z.total_seats
        db.add(z)

    db.commit()
