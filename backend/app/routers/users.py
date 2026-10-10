from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_db
from app.models import Booking, User
from app.security import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/users", tags=["User Management"])


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None  # เฉพาะ admin เท่านั้นที่เปลี่ยนได้


def _public(u: User) -> dict:
    return {"id": u.id, "username": u.username, "email": u.email, "role": u.role}


def _get_target(db: Session, user_id: int, me: User) -> User:
    """เจ้าของบัญชีหรือ admin เท่านั้น (คนอื่นได้ 404 เพื่อไม่ให้เดา id ได้)"""
    target = db.get(User, user_id)
    if not target or (target.id != me.id and me.role != "admin"):
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งานนี้")
    return target


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """ดึงข้อมูลโปรไฟล์ของตัวเอง"""
    return _public(user)


@router.get("/check-username/{name}")
def check_username(name: str, db: Session = Depends(get_db)):
    """ตรวจสอบ username ว่างไหม"""
    taken = db.exec(select(User).where(User.username == name.strip())).first()
    return {"username": name, "available": taken is None}


@router.get("/")
def get_all_users(
    skip: int = 0,
    limit: int = 10,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """ดึงข้อมูล user ทั้งหมด (เฉพาะ admin)"""
    limit = min(max(limit, 1), 100)
    users = db.exec(select(User).order_by(User.id).offset(max(skip, 0)).limit(limit)).all()
    return [_public(u) for u in users]


@router.get("/{id}")
def get_user_by_id(
    id: int, me: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return _public(_get_target(db, id, me))


@router.put("/{id}")
def update_user(
    id: int,
    data: UserUpdate,
    me: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _get_target(db, id, me)

    if data.email is not None:
        email = data.email.strip()
        dup = db.exec(select(User).where(User.email == email, User.id != target.id)).first()
        if dup:
            raise HTTPException(status_code=400, detail="Email นี้ถูกใช้งานแล้ว")
        target.email = email

    if data.role is not None:
        if me.role != "admin":
            raise HTTPException(status_code=403, detail="เฉพาะผู้ดูแลระบบเท่านั้นที่เปลี่ยนสิทธิ์ได้")
        if data.role not in ("customer", "admin"):
            raise HTTPException(status_code=400, detail="role ต้องเป็น customer หรือ admin")
        target.role = data.role

    db.add(target)
    db.commit()
    db.refresh(target)
    return {"message": "อัปเดตข้อมูลผู้ใช้งานสำเร็จ", "user": _public(target)}


@router.delete("/{id}")
def delete_user(
    id: int, me: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    target = _get_target(db, id, me)
    has_booking = db.exec(select(Booking).where(Booking.user_id == target.id)).first()
    if has_booking:
        raise HTTPException(status_code=409, detail="ลบไม่ได้ เพราะยังมีรายการจองผูกกับบัญชีนี้")
    db.delete(target)
    db.commit()
    return {"id": id, "message": "ลบผู้ใช้งานสำเร็จ"}
