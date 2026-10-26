"""
presenters.py
--------------
แปลงข้อมูลจากตาราง (models) เป็นรูปแบบที่ส่งออก API (schemas)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session

from app import crud
from app.models import Booking, Ticket
from app.schemas import AdminBookingOut, BookingOut, TicketOut

TH_TZ = timezone(timedelta(hours=7))

STATUS_LABELS = {
    "pending": "ล็อกที่นั่งแล้ว รอกรอกข้อมูล",
    "awaiting_payment": "รอชำระเงิน",
    "pending_review": "รอตรวจสอบสลิป",
    "rejected": "สลิปไม่ผ่าน กรุณาแนบใหม่",
    "paid": "ชำระเงินแล้ว",
    "cancelled": "ยกเลิกแล้ว",
    "expired": "หมดเวลา",
}


def fmt_th(dt: Optional[datetime]) -> Optional[str]:
    """เวลา UTC (naive) -> ข้อความเวลาไทย เช่น 26/10/2026 23:45"""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TH_TZ).strftime("%d/%m/%Y %H:%M")


def _base_fields(db: Session, b: Booking) -> dict:
    race = crud.get_race(db, b.race_id)
    zone = crud.get_zone(db, b.zone_id)
    status = "expired" if crud.is_expired(b) else b.status  # หมดเวลาแล้วแต่ scheduler ยังไม่มาเก็บ
    return dict(
        id=b.id,
        race_id=b.race_id,
        zone_id=b.zone_id,
        race_name=race.name if race else "-",
        race_date=race.race_date if race else "-",
        zone_name=zone.name if zone else "-",
        quantity=b.quantity,
        total_price=b.total_price,
        status=status,
        status_label=STATUS_LABELS.get(status, status),
        buyer_name=b.buyer_name,
        buyer_phone=b.buyer_phone,
        payment_method=b.payment_method,
        seconds_left=crud.seconds_left(b) if status != "expired" else 0,
        slip_uploaded=b.slip_uploaded_at is not None,
        reject_reason=b.reject_reason,
        has_ticket=status == "paid",
    )


def booking_out(db: Session, b: Booking) -> BookingOut:
    return BookingOut(**_base_fields(db, b))


def admin_booking_out(db: Session, b: Booking) -> AdminBookingOut:
    owner = crud.get_user(db, b.user_id)
    reviewer = crud.get_user(db, b.reviewed_by)
    ticket = crud.get_ticket(db, b.id) if b.status == "paid" else None
    return AdminBookingOut(
        **_base_fields(db, b),
        username=owner.username if owner else None,
        created_at=fmt_th(b.created_at),
        slip_uploaded_at=fmt_th(b.slip_uploaded_at),
        duplicate_of=crud.find_slip_duplicates(db, b.slip_hash, b.id) if b.slip_hash else [],
        verify_note=b.verify_note,
        reviewed_by=reviewer.username if reviewer else ("ระบบอัตโนมัติ" if b.reviewed_at else None),
        reviewed_at=fmt_th(b.reviewed_at),
        ticket_code=ticket.ticket_code if ticket else None,
        checked_in_at=fmt_th(ticket.checked_in_at) if ticket else None,
    )


def ticket_out(db: Session, booking: Booking, ticket: Ticket) -> TicketOut:
    race = crud.get_race(db, booking.race_id)
    zone = crud.get_zone(db, booking.zone_id)
    return TicketOut(
        booking_id=booking.id,
        ticket_code=ticket.ticket_code,
        qr_code_data=ticket.qr_code_data,
        race_name=race.name if race else "-",
        zone_name=zone.name if zone else "-",
        quantity=booking.quantity,
        buyer_name=booking.buyer_name or "-",
        venue=race.venue if race else "-",
        race_date=race.race_date if race else "-",
        checked_in_at=fmt_th(ticket.checked_in_at),
    )
