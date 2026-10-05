"""
routers/bookings.py
---------------------
Endpoint ที่เกี่ยวกับ "การจอง / ชำระเงิน / ตั๋ว / ยกเลิก"
ตรงกับขั้นตอนที่ 3-6 ในตาราง User Journey:
    3. เลือกโซน & จำนวนตั๋ว      -> POST /api/bookings (ล็อกที่นั่งชั่วคราว)
    4. กรอกข้อมูลผู้เข้าชม        -> POST /api/bookings/{id}/checkout
    5. ชำระเงิน                 -> POST /api/bookings/{id}/payment
    6. รับ e-Ticket              -> GET  /api/bookings/{id}/ticket
    7. ยกเลิกการจอง              -> POST /api/bookings/{id}/cancel
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app import crud
from app.database import get_db
from app.schemas import (
    BookingCreate,
    BookingOut,
    CheckoutInfo,
    PaymentRequest,
    TicketOut,
)

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    """POST /api/bookings — ล็อกที่นั่งชั่วคราวตามโซน+จำนวนที่เลือก"""
    booking = crud.create_booking(db, payload.race_id, payload.zone_id, payload.quantity)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ที่นั่งในโซนนี้ไม่พอ กรุณาเลือกโซนอื่นหรือลดจำนวน"
        )
    return booking


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """GET /api/bookings/{booking_id} — ดูสรุปการจองปัจจุบัน"""
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบการจองนี้ (อาจหมดเวลาล็อกที่นั่งแล้ว)"
        )
    return booking


@router.post("/{booking_id}/checkout", response_model=BookingOut)
def submit_checkout_info(
    booking_id: int, 
    payload: CheckoutInfo, 
    db: Session = Depends(get_db)
):
    """POST /api/bookings/{booking_id}/checkout — บันทึกข้อมูลผู้ซื้อ+ช่องทางชำระเงิน"""
    booking = crud.update_checkout_info(
        db, booking_id, payload.buyer_name, payload.buyer_phone, payload.payment_method
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบการจองนี้"
        )
    return booking


@router.post("/{booking_id}/payment", response_model=TicketOut)
def process_payment(
    booking_id: int, 
    payload: PaymentRequest, 
    db: Session = Depends(get_db)
):
    """POST /api/bookings/{booking_id}/payment — ประมวลผลการชำระเงิน แล้วออก e-Ticket"""
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบการจองนี้"
        )

    ticket = crud.confirm_payment(db, booking_id, payload.payment_method)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถชำระเงินสำหรับการจองนี้ได้"
        )

    race = crud.get_race(db, booking.race_id)
    zone = crud.get_zone(db, booking.zone_id)

    return TicketOut(
        booking_id=booking_id,
        ticket_code=ticket.ticket_code,
        qr_code_data=ticket.qr_code_data,
        race_name=race.name if race else "-",
        zone_name=zone.name if zone else "-",
        quantity=booking.quantity,
        buyer_name=booking.buyer_name or "-",
        venue=race.venue if race else "-",
        race_date=race.race_date if race else "-",
    )


@router.get("/{booking_id}/ticket", response_model=TicketOut)
def get_ticket(booking_id: int, db: Session = Depends(get_db)):
    """GET /api/bookings/{booking_id}/ticket — เรียกดู e-Ticket ที่ออกแล้ว"""
    booking = crud.get_booking(db, booking_id)
    ticket = crud.get_ticket(db, booking_id)
    if not booking or not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ยังไม่พบ e-Ticket สำหรับการจองนี้"
        )

    race = crud.get_race(db, booking.race_id)
    zone = crud.get_zone(db, booking.zone_id)

    return TicketOut(
        booking_id=booking_id,
        ticket_code=ticket.ticket_code,
        qr_code_data=ticket.qr_code_data,
        race_name=race.name if race else "-",
        zone_name=zone.name if zone else "-",
        quantity=booking.quantity,
        buyer_name=booking.buyer_name or "-",
        venue=race.venue if race else "-",
        race_date=race.race_date if race else "-",
    )


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    """POST /api/bookings/{booking_id}/cancel — ยกเลิกรายการจองและคืนที่นั่งเข้า Zone"""
    success = crud.cancel_booking(db, booking_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ไม่สามารถยกเลิกการจองนี้ได้ (อาจถูกยกเลิกไปแล้ว หรือชำระเงินเรียบร้อยแล้ว)"
        )
    return {"status": "success", "message": f"ยกเลิกการจอง #{booking_id} และคืนที่นั่งเรียบร้อยแล้ว"}