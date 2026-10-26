"""
routers/checkin.py — สแกนตั๋วเข้างาน (role staff หรือ admin)
    POST /api/checkin   body: {"code": "<ข้อความใน QR> หรือ TIX-000123"}
สแกนผ่านครั้งแรก = บันทึกเวลาเข้างาน ครั้งถัดไปจะได้ผล already_used
ถ้าวันที่ไม่ตรงวันแข่ง จะได้ผล wrong_day (ยังไม่บันทึก) ต้องส่ง force=true เพื่อยืนยันให้เข้า
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import crud
from app.database import get_db
from app.models import User
from app.presenters import TH_TZ, fmt_th
from app.schemas import CheckInRequest, CheckInResult
from app.security import require_staff

router = APIRouter(prefix="/api/checkin", tags=["check-in"])


@router.post("", response_model=CheckInResult)
def scan(payload: CheckInRequest, staff: User = Depends(require_staff), db: Session = Depends(get_db)):
    ticket = crud.find_ticket_by_code(db, payload.code)
    if not ticket:
        return CheckInResult(result="not_found", message="ไม่พบตั๋วนี้ในระบบ")

    booking = crud.get_booking(db, ticket.booking_id)
    race = crud.get_race(db, booking.race_id) if booking else None
    zone = crud.get_zone(db, booking.zone_id) if booking else None
    info = dict(
        ticket_code=ticket.ticket_code,
        race_name=race.name if race else None,
        race_date=race.race_date if race else None,
        zone_name=zone.name if zone else None,
        quantity=booking.quantity if booking else None,
        buyer_name=booking.buyer_name if booking else None,
    )

    if not booking or booking.status != "paid":
        db.rollback()
        return CheckInResult(result="not_paid", message="ตั๋วนี้ยังไม่ได้รับการยืนยันการชำระเงิน", **info)

    if ticket.checked_in_at:
        db.rollback()
        return CheckInResult(
            result="already_used",
            message=f"ตั๋วนี้ถูกใช้เข้างานไปแล้วเมื่อ {fmt_th(ticket.checked_in_at)}",
            checked_in_at=fmt_th(ticket.checked_in_at),
            **info,
        )

    date_warning = None
    today = datetime.now(TH_TZ).strftime("%d/%m/%Y")
    if race and race.race_date != today:
        date_warning = f"ตั๋วนี้สำหรับวันที่ {race.race_date} แต่วันนี้คือ {today}"
        if not payload.force:
            db.rollback()
            return CheckInResult(
                result="wrong_day",
                message="ตั๋วไม่ตรงวันแข่ง ยังไม่ได้บันทึกเข้างาน",
                date_warning=date_warning,
                **info,
            )

    crud.check_in(db, ticket, staff.id)
    return CheckInResult(
        result="ok",
        message=f"ตั๋วถูกต้อง เข้างานได้ {booking.quantity} คน",
        checked_in_at=fmt_th(ticket.checked_in_at),
        date_warning=date_warning,
        **info,
    )
