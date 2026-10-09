"""
routers/bookings.py
---------------------
ทุก endpoint ต้องล็อกอิน และเข้าถึงได้เฉพาะการจองของตัวเอง (admin ดูได้ทั้งหมด)
    POST /api/bookings                  เลือกโซน & จำนวน (ล็อกที่นั่งชั่วคราว)
    POST /api/bookings/{id}/checkout    กรอกข้อมูลผู้เข้าชม
    POST /api/bookings/{id}/payment     ชำระเงิน (ยังเป็น demo จะปิดในรอบที่ 4)
    GET  /api/bookings/{id}/ticket      ดู e-Ticket
    POST /api/bookings/{id}/cancel      ยกเลิก
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud
from app.database import get_db
from app.models import Booking, User
from app.schemas import (
    BookingCreate,
    BookingOut,
    CheckoutInfo,
    PaymentRequest,
    TicketOut,
)
from app.security import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _owned_booking(db: Session, booking_id: int, user: User, msg: str = "ไม่พบการจองนี้") -> Booking:
    """ดึงการจองที่เป็นของ user นี้เท่านั้น ถ้าไม่ใช่ตอบ 404 (ไม่บอกว่ามีอยู่จริง)"""
    booking = crud.get_booking(db, booking_id)
    if not booking or (booking.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    return booking


def _ticket_out(db: Session, booking: Booking, ticket) -> TicketOut:
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
    )


@router.post("", response_model=BookingOut)
def create_booking(
    payload: BookingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = crud.create_booking(db, payload.race_id, payload.zone_id, payload.quantity)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ที่นั่งในโซนนี้ไม่พอ กรุณาเลือกโซนอื่นหรือลดจำนวน",
        )
    booking.user_id = user.id
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(
    booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _owned_booking(db, booking_id, user, "ไม่พบการจองนี้ (อาจหมดเวลาล็อกที่นั่งแล้ว)")


@router.post("/{booking_id}/checkout", response_model=BookingOut)
def submit_checkout_info(
    booking_id: int,
    payload: CheckoutInfo,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_booking(db, booking_id, user)
    booking = crud.update_checkout_info(
        db, booking_id, payload.buyer_name, payload.buyer_phone, payload.payment_method
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบการจองนี้")
    return booking


@router.post("/{booking_id}/payment", response_model=TicketOut)
def process_payment(
    booking_id: int,
    payload: PaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = _owned_booking(db, booking_id, user)
    ticket = crud.confirm_payment(db, booking_id, payload.payment_method)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถชำระเงินสำหรับการจองนี้ได้",
        )
    return _ticket_out(db, booking, ticket)


@router.get("/{booking_id}/ticket", response_model=TicketOut)
def get_ticket(
    booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    booking = _owned_booking(db, booking_id, user, "ยังไม่พบ e-Ticket สำหรับการจองนี้")
    ticket = crud.get_ticket(db, booking_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ยังไม่พบ e-Ticket สำหรับการจองนี้"
        )
    return _ticket_out(db, booking, ticket)


@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    _owned_booking(db, booking_id, user)
    if not crud.cancel_booking(db, booking_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถยกเลิกการจองนี้ได้ (อาจถูกยกเลิกไปแล้ว หรือชำระเงินเรียบร้อยแล้ว)",
        )
    return {"status": "success", "message": f"ยกเลิกการจอง #{booking_id} และคืนที่นั่งเรียบร้อยแล้ว"}
