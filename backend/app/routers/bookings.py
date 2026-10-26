"""
routers/bookings.py
---------------------
ทุก endpoint ต้องล็อกอิน และเข้าถึงได้เฉพาะการจองของตัวเอง (admin ดูได้ทั้งหมด)
    POST /api/bookings                     เลือกโซน & จำนวน (ล็อกที่นั่งชั่วคราว)
    GET  /api/bookings/mine                การจอง/ตั๋วทั้งหมดของฉัน
    GET  /api/bookings/{id}                สถานะการจอง
    POST /api/bookings/{id}/checkout       กรอกข้อมูลผู้เข้าชม
    GET  /api/bookings/{id}/payment-info   ข้อมูล QR พร้อมเพย์ (ฝังยอดเงินแล้ว)
    POST /api/bookings/{id}/slip           แนบสลิปโอนเงิน -> รอแอดมินตรวจ
    GET  /api/bookings/{id}/ticket         ดู e-Ticket (หลังอนุมัติแล้ว)
    POST /api/bookings/{id}/cancel         ยกเลิก (ก่อนส่งสลิป)
"""

import hashlib
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app import config, crud, promptpay, slip_verify
from app.database import get_db
from app.models import Booking, User
from app.presenters import booking_out, ticket_out
from app.schemas import BookingCreate, BookingOut, CheckoutInfo, PaymentInfo, TicketOut
from app.security import get_current_user

router = APIRouter(prefix="/api/bookings", tags=["bookings"])

# ตรวจชนิดไฟล์จาก "ไบต์แรกของไฟล์" ไม่เชื่อนามสกุล/Content-Type ที่ผู้ใช้ส่งมา
_IMAGE_SIGNATURES = (
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png", "image/png"),
)


def _detect_image(head: bytes):
    for sig, ext, mime in _IMAGE_SIGNATURES:
        if head.startswith(sig):
            return ext, mime
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp", "image/webp"
    return None


def _raise(e: crud.BookingError):
    raise HTTPException(status_code=e.status_code, detail=e.message)


def _owned_booking(db: Session, booking_id: int, user: User, msg: str = "ไม่พบการจองนี้") -> Booking:
    """ดึงการจองที่เป็นของ user นี้เท่านั้น ถ้าไม่ใช่ตอบ 404 (ไม่บอกว่ามีอยู่จริง)"""
    booking = crud.get_booking(db, booking_id)
    if not booking or (booking.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    return booking


def _mask_id(raw: str) -> str:
    digits = "".join(ch for ch in raw if ch.isdigit())
    return ("x" * max(0, len(digits) - 4)) + digits[-4:]


@router.post("", response_model=BookingOut)
def create_booking(
    payload: BookingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        booking = crud.create_booking(db, user.id, payload.race_id, payload.zone_id, payload.quantity)
    except crud.BookingError as e:
        _raise(e)
    return booking_out(db, booking)


@router.get("/mine", response_model=List[BookingOut])
def my_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [booking_out(db, b) for b in crud.list_user_bookings(db, user.id)]


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return booking_out(db, _owned_booking(db, booking_id, user))


@router.post("/{booking_id}/checkout", response_model=BookingOut)
def submit_checkout_info(
    booking_id: int,
    payload: CheckoutInfo,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_booking(db, booking_id, user)
    try:
        booking = crud.update_checkout_info(db, booking_id, payload.buyer_name, payload.buyer_phone)
    except crud.BookingError as e:
        _raise(e)
    return booking_out(db, booking)


@router.get("/{booking_id}/payment-info", response_model=PaymentInfo)
def payment_info(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = _owned_booking(db, booking_id, user)
    info = PaymentInfo(booking=booking_out(db, booking), amount=booking.total_price)
    if not config.PROMPTPAY_ID:
        info.config_error = "ร้านยังไม่ได้ตั้งค่าเลขพร้อมเพย์ (PROMPTPAY_ID ในไฟล์ .env)"
        return info
    try:
        info.promptpay_payload = promptpay.build_payload(config.PROMPTPAY_ID, booking.total_price)
    except ValueError as e:
        info.config_error = str(e)
        return info
    info.promptpay_name = config.PROMPTPAY_NAME or None
    info.promptpay_masked_id = _mask_id(config.PROMPTPAY_ID)
    return info


@router.post("/{booking_id}/slip", response_model=BookingOut)
def upload_slip(
    booking_id: int,
    file: UploadFile = File(..., description="รูปสลิป JPG / PNG / WEBP ไม่เกิน 5MB"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = _owned_booking(db, booking_id, user)
    try:
        # เช็กเบื้องต้นก่อนเขียนไฟล์ (เช็กซ้ำแบบล็อกแถวอีกครั้งใน crud.attach_slip)
        crud.assert_can_attach_slip(db, booking)
    except crud.BookingError as e:
        _raise(e)

    data = file.file.read(config.MAX_SLIP_BYTES + 1)
    if len(data) > config.MAX_SLIP_BYTES:
        raise HTTPException(status_code=413, detail=f"ไฟล์ใหญ่เกิน {config.MAX_SLIP_BYTES // (1024 * 1024)}MB")
    detected = _detect_image(data[:16])
    if not detected:
        raise HTTPException(status_code=400, detail="รองรับเฉพาะรูปภาพ JPG, PNG หรือ WEBP")
    ext, mime = detected

    filename = f"slip_{booking_id}.{ext}"
    try:
        booking = crud.attach_slip(db, booking_id, data, mime, hashlib.sha256(data).hexdigest())
    except crud.BookingError as e:
        _raise(e)

    # ตรวจสลิปอัตโนมัติ (ถ้าเปิดใช้) — ไม่ผ่าน/ล่ม = ปล่อยให้แอดมินตรวจตามปกติ
    result = slip_verify.verify_slip(
        data, filename, mime, float(booking.total_price), crud.as_utc_naive(booking.created_at),
        lambda ref: crud.slip_ref_used(db, ref, booking_id),
    )
    if result:
        crud.set_verify_result(db, booking_id, result.note, result.ref)
        if result.approved:
            try:
                crud.approve_booking(db, booking_id, reviewer_id=None)
            except crud.BookingError:
                pass
        db.refresh(booking)

    return booking_out(db, booking)


@router.get("/{booking_id}/ticket", response_model=TicketOut)
def get_ticket(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = _owned_booking(db, booking_id, user, "ยังไม่พบ e-Ticket สำหรับการจองนี้")
    ticket = crud.get_ticket(db, booking_id) if booking.status == "paid" else None
    if not ticket:
        raise HTTPException(status_code=404, detail="ยังไม่พบ e-Ticket สำหรับการจองนี้")
    return ticket_out(db, booking, ticket)


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_booking(db, booking_id, user)
    try:
        crud.cancel_booking(db, booking_id, by_admin=False)
    except crud.BookingError as e:
        _raise(e)
    return {"status": "success", "message": f"ยกเลิกการจอง #{booking_id} และคืนที่นั่งเรียบร้อยแล้ว"}
