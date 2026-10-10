"""
security.py
-----------
hash รหัสผ่าน (bcrypt) + ออก/ตรวจ JWT + dependency get_current_user
"""

import hmac
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.database import get_db
from app.models import User

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise RuntimeError(
        "ต้องตั้ง SECRET_KEY ใน .env (ยาวอย่างน้อย 32 ตัวอักษร) "
        "สร้างได้ด้วย: openssl rand -hex 32"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

bearer_scheme = HTTPBearer(auto_error=False)


# ---------- รหัสผ่าน ----------
def hash_password(plain: str) -> str:
    # bcrypt อ่านแค่ 72 ไบต์แรก
    return bcrypt.hashpw(plain.encode()[:72], bcrypt.gensalt()).decode()


def is_hashed(stored: str) -> bool:
    """เช็กว่าค่าที่เก็บเป็น bcrypt hash แล้วหรือยัง (ของเก่าเป็นข้อความธรรมดา)"""
    return len(stored) == 60 and stored.startswith(("$2a$", "$2b$", "$2y$"))


def verify_password(plain: str, stored: str) -> bool:
    if is_hashed(stored):
        try:
            return bcrypt.checkpw(plain.encode()[:72], stored.encode())
        except ValueError:
            return False
    # user เก่าที่ยังเป็นข้อความธรรมดา (เทียบแบบกัน timing attack)
    return hmac.compare_digest(plain.encode(), stored.encode())


# ---------- JWT ----------
def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _unauthorized(detail: str = "กรุณาเข้าสู่ระบบ") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _unauthorized()
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise _unauthorized("เซสชันหมดอายุ กรุณาเข้าสู่ระบบใหม่")
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _unauthorized("Token ไม่ถูกต้อง กรุณาเข้าสู่ระบบใหม่")

    user = db.get(User, user_id)
    if not user:
        raise _unauthorized("ไม่พบบัญชีผู้ใช้นี้")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="เฉพาะผู้ดูแลระบบเท่านั้น")
    return user
