"""
database.py
------------
เตรียมการเชื่อมต่อฐานข้อมูล PostgreSQL ด้วย SQLModel
"""

import os
from sqlmodel import SQLModel, create_engine, Session

# อ่านค่า connection string จาก environment variable (DATABASE_URL)
# ตัวอย่างค่าใน .env: DATABASE_URL=postgresql://appuser:apppassword@db:5432/appdb
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://appuser:apppassword@db:5432/appdb",
)

# echo=False ปิด log SQL (เปลี่ยนเป็น True ตอน debug ได้)
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """สร้างตารางทั้งหมดตาม model ใน models.py (ใช้ตอนเริ่มต้นระบบ/dev เท่านั้น)"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency สำหรับ FastAPI: with session ต่อ 1 request แล้วปิดอัตโนมัติ"""
    with Session(engine) as session:
        yield session


def get_db():
    """Dependency เสริมสำหรับรองรับ auth.py ที่เรียกใช้ get_db"""
    with Session(engine) as session:
        yield session