"""
routers/admin.py — หลังบ้านสำหรับแอดมิน (ต้องเป็น role admin)
    GET  /api/admin/summary                  ตัวเลขสรุป + ที่นั่งแต่ละโซน
    GET  /api/admin/bookings?status=...      รายการจอง (ค่าเริ่มต้น: รอตรวจสลิป เก่าสุดก่อน)
    GET  /api/admin/bookings/{id}/slip       ไฟล์รูปสลิป
    POST /api/admin/bookings/{id}/approve    อนุมัติ -> ออก e-Ticket
    POST /api/admin/bookings/{id}/reject     ปฏิเสธ (ให้แนบใหม่ หรือยกเลิกคืนที่นั่ง)
    POST /api/admin/bookings/{id}/cancel     ยกเลิกการจองที่ยังไม่จ่าย + คืนที่นั่ง
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlmodel import Session

from app import config, crud
from app.database import get_db
from app.models import User
from app.presenters import STATUS_LABELS, admin_booking_out
from app.schemas import AdminBookingOut, RejectRequest
from app.security import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

_MIME = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


def _raise(e: crud.BookingError):
    raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/summary")
def summary(_admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    counts = crud.status_counts(db)
    sold = crud.sold_seats_by_zone(db)
    races = []
    for race in crud.list_races(db):
        races.append({
            "id": race.id,
            "name": race.name,
            "race_date": race.race_date,
            "zones": [
                {
                    "id": z.id,
                    "name": z.name,
                    "price": z.price,
                    "total_seats": z.total_seats,
                    "available_seats": z.available_seats,
                    "sold_seats": sold.get(z.id, 0),
                }
                for z in crud.list_zones(db, race.id)
            ],
        })
    return {
        "counts": {s: counts.get(s, 0) for s in STATUS_LABELS},
        "status_labels": STATUS_LABELS,
        "pending_review": counts.get("pending_review", 0),
        "paid_revenue": crud.paid_revenue(db),
        "races": races,
        "slip_verify_provider": config.SLIP_VERIFY_PROVIDER,
        "promptpay_configured": bool(config.PROMPTPAY_ID),
    }


@router.get("/bookings", response_model=List[AdminBookingOut])
def list_bookings(
    status: Optional[str] = Query(default="pending_review", description="ว่าง = ทุกสถานะ"),
    limit: int = Query(default=100, ge=1, le=500),
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if status and status not in STATUS_LABELS:
        raise HTTPException(status_code=400, detail="สถานะไม่ถูกต้อง")
    return [admin_booking_out(db, b) for b in crud.admin_list_bookings(db, status or None, limit)]


@router.get("/bookings/{booking_id}", response_model=AdminBookingOut)
def get_booking(booking_id: int, _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    booking = crud.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="ไม่พบการจองนี้")
    return admin_booking_out(db, booking)


@router.get("/bookings/{booking_id}/slip")
def get_slip(booking_id: int, _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    booking = crud.get_booking(db, booking_id)
    if not booking or not booking.slip_path:
        raise HTTPException(status_code=404, detail="การจองนี้ยังไม่มีสลิป")
    path = (config.UPLOAD_DIR / booking.slip_path).resolve()
    if path.parent != config.UPLOAD_DIR.resolve() or not path.is_file():
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์สลิป")
    ext = path.suffix.lstrip(".").lower()
    return FileResponse(path, media_type=_MIME.get(ext, "application/octet-stream"),
                        headers={"Cache-Control": "private, no-store"})


@router.post("/bookings/{booking_id}/approve", response_model=AdminBookingOut)
def approve(booking_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        crud.approve_booking(db, booking_id, reviewer_id=admin.id)
    except crud.BookingError as e:
        _raise(e)
    return admin_booking_out(db, crud.get_booking(db, booking_id))


@router.post("/bookings/{booking_id}/reject", response_model=AdminBookingOut)
def reject(
    booking_id: int,
    payload: RejectRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        booking = crud.reject_booking(db, booking_id, admin.id, payload.reason.strip(), payload.allow_reupload)
    except crud.BookingError as e:
        _raise(e)
    return admin_booking_out(db, booking)


@router.post("/bookings/{booking_id}/cancel", response_model=AdminBookingOut)
def cancel(booking_id: int, _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        booking = crud.cancel_booking(db, booking_id, by_admin=True)
    except crud.BookingError as e:
        _raise(e)
    return admin_booking_out(db, booking)
