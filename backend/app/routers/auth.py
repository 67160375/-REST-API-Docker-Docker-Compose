from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_db
from app.models import User
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    is_hashed,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

MIN_PASSWORD_LEN = 8


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    """สมัครสมาชิกใหม่ (เก็บรหัสผ่านแบบ hash)"""
    username = data.username.strip()
    email = data.email.strip()

    if not username or not data.password or not email:
        raise HTTPException(status_code=400, detail="กรุณากรอกข้อมูลให้ครบถ้วนทุกช่อง")
    if len(data.password) < MIN_PASSWORD_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"รหัสผ่านต้องยาวอย่างน้อย {MIN_PASSWORD_LEN} ตัวอักษร",
        )

    existing = db.exec(
        select(User).where((User.username == username) | (User.email == email))
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username หรือ Email นี้ถูกใช้งานแล้ว")

    new_user = User(
        username=username,
        email=email,
        password=hash_password(data.password),
        role="customer",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"status": "success", "message": "สมัครสมาชิกสำเร็จเรียบร้อยแล้ว!"}


@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    """เข้าสู่ระบบ แล้วออก JWT จริง"""
    if not data.username or not data.password:
        raise HTTPException(status_code=400, detail="กรุณากรอก Username และ Password")

    user = db.exec(select(User).where(User.username == data.username)).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
        )

    # user เก่าที่รหัสผ่านยังเป็นข้อความธรรมดา: hash ให้ตอนล็อกอินสำเร็จ
    if not is_hashed(user.password):
        user.password = hash_password(data.password)
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "status": "success",
        "access_token": create_access_token(user),
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
    """JWT ไม่เก็บสถานะที่ server ฝั่ง client ลบ token เองตอนออกจากระบบ"""
    return {"status": "success", "message": "ออกจากระบบสำเร็จ"}


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """เปลี่ยนรหัสผ่านของตัวเอง (ต้องล็อกอิน)"""
    if not verify_password(data.old_password, user.password):
        raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")
    if len(data.new_password) < MIN_PASSWORD_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"รหัสผ่านใหม่ต้องยาวอย่างน้อย {MIN_PASSWORD_LEN} ตัวอักษร",
        )

    user.password = hash_password(data.new_password)
    db.add(user)
    db.commit()
    return {"status": "success", "message": "เปลี่ยนรหัสผ่านสำเร็จเรียบร้อยแล้ว"}
