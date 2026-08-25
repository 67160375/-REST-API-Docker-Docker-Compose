from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    username: str
    old_password: str
    new_password: str


@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    """สมัครสมาชิกใหม่ ลง PostgreSQL"""
    if not data.username or not data.password or not data.email:
        raise HTTPException(
            status_code=400, detail="กรุณากรอกข้อมูลให้ครบถ้วนทุกช่อง"
        )

    # ตรวจสอบว่ามี username หรือ email ซ้ำใน DB หรือไม่
    statement = select(User).where(
        (User.username == data.username) | (User.email == data.email)
    )
    existing_user = db.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=400, detail="Username หรือ Email นี้ถูกใช้งานแล้ว"
        )

    # บันทึกผู้ใช้ใหม่ลงฐานข้อมูลจริง
    new_user = User(
        username=data.username,
        email=data.email,
        password=data.password,
        role="customer",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "status": "success",
        "message": "สมัครสมาชิกสำเร็จเรียบร้อยแล้ว!",
    }


@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    """เข้าสู่ระบบ โดยเช็กชื่อผู้ใช้และรหัสผ่านจาก PostgreSQL"""
    if not data.username or not data.password:
        raise HTTPException(
            status_code=400, detail="กรุณากรอก Username และ Password"
        )

    # ค้นหา User ใน PostgreSQL
    statement = select(User).where(User.username == data.username)
    user = db.exec(statement).first()

    # หากไม่มีผู้ใช้ หรือรหัสผ่านไม่ตรงกัน ให้ปฏิเสธการล็อกอิน
    if not user or user.password != data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
        )

    return {
        "status": "success",
        "access_token": f"jwt_token_user_{user.id}",
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
        "message": "เข้าสู่ระบบสำเร็จ!",
    }


@router.post("/logout")
def logout_user():
    """ออกจากระบบ"""
    return {"status": "success", "message": "ออกจากระบบสำเร็จ"}


@router.post("/change-password")
def change_password(data: ChangePasswordRequest, db: Session = Depends(get_db)):
    """เปลี่ยนรหัสผ่านใน PostgreSQL"""
    statement = select(User).where(User.username == data.username)
    user = db.exec(statement).first()

    if not user or user.password != data.old_password:
        raise HTTPException(
            status_code=400, detail="ชื่อผู้ใช้หรือรหัสผ่านเดิมไม่ถูกต้อง"
        )

    user.password = data.new_password
    db.add(user)
    db.commit()

    return {"status": "success", "message": "เปลี่ยนรหัสผ่านสำเร็จเรียบร้อยแล้ว"}