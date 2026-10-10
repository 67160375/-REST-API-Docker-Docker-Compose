"""
database.py
------------
เตรียมการเชื่อมต่อฐานข้อมูล PostgreSQL ด้วย SQLModel
รองรับ Retry Mechanism เพื่อป้องกัน Startup OperationalError
"""

import os
import time
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import OperationalError

# อ่านค่า connection string จาก environment variable (DATABASE_URL)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://appuser:apppassword@db:5432/appdb",
)

# echo=False ปิด log SQL (เปลี่ยนเป็น True ตอน debug ได้)
engine = create_engine(DATABASE_URL, echo=False)


def init_db(max_retries: int = 10, delay: int = 2) -> None:
    """
    สร้างตารางทั้งหมดตาม model ใน models.py
    พร้อมระบบ Retry เมื่อฐานข้อมูลอยู่ในช่วงกำลังสตาร์ท
    """
    for attempt in range(1, max_retries + 1):
        try:
            SQLModel.metadata.create_all(engine)
            print("Database connected and tables initialized successfully.")
            return
        except OperationalError as e:
            if attempt == max_retries:
                print(f"Failed to connect to database after {max_retries} attempts.")
                raise e
            print(f"Database not ready yet (attempt {attempt}/{max_retries}). Retrying in {delay}s...")
            time.sleep(delay)


def get_session():
    """Dependency สำหรับ FastAPI: with session ต่อ 1 request แล้วปิดอัตโนมัติ"""
    with Session(engine) as session:
        yield session


def get_db():
    """Dependency เสริมสำหรับรองรับ auth.py ที่เรียกใช้ get_db"""
    with Session(engine) as session:
        yield session