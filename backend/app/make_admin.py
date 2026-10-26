"""
make_admin.py — ตั้งสิทธิ์ให้ผู้ใช้ที่สมัครไว้แล้ว (ทำครั้งแรกตอนยังไม่มีแอดมินเลย)

วิธีใช้ (สมัครสมาชิกผ่านหน้าเว็บก่อน แล้วรัน):
    docker compose exec web python -m app.make_admin <username>            -> admin
    docker compose exec web python -m app.make_admin <username> staff      -> พนักงานสแกนตั๋ว
    docker compose exec web python -m app.make_admin <username> customer   -> ถอดสิทธิ์
"""

import sys

from sqlmodel import Session, select

from app.database import engine
from app.models import User

ROLES = ("admin", "staff", "customer")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    username = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "admin"
    if role not in ROLES:
        print(f"role ต้องเป็นหนึ่งใน {', '.join(ROLES)}")
        return 1
    with Session(engine) as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f"ไม่พบผู้ใช้ '{username}' (สมัครสมาชิกผ่านหน้าเว็บก่อน)")
            return 1
        user.role = role
        db.add(user)
        db.commit()
    print(f"ตั้งสิทธิ์ '{username}' เป็น {role} แล้ว (ให้ผู้ใช้ออกจากระบบแล้วล็อกอินใหม่)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
