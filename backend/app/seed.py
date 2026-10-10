"""
seed.py
--------
ใส่ข้อมูลรายการแข่ง + โซนที่นั่ง ตอนเริ่มระบบ ถ้าตาราง Race ยังว่างอยู่
ถ้ามีรายการแข่งอยู่แล้ว จะไม่ทำอะไรเลย (รันซ้ำกี่ครั้งก็ปลอดภัย)

หมายเหตุ: ชื่อ/วันที่/สนาม/ราคาเริ่มต้นของ 3 รายการมาจากหน้าเว็บเดิม
ส่วนชื่อโซน ราคาแต่ละโซน และจำนวนที่นั่ง เป็นค่าสมมติ แก้ได้ตามจริง
(ราคาโซนที่ถูกที่สุดต้องเท่ากับ price_from ของรายการนั้น)
"""

from sqlmodel import Session, select

from app.database import engine
from app.models import Race, Zone

_VENUE = "ช้าง อินเตอร์เนชั่นแนล เซอร์กิต จ.บุรีรัมย์"

# โซนเป็น (ชื่อโซน, ราคา, จำนวนที่นั่ง)
_SAMPLE_RACES = [
    {
        "name": "Thailand Super Series 2026",
        "category": "รถยนต์ทางเรียบ",
        "race_date": "15/08/2026",
        "venue": _VENUE,
        "price_from": 500,
        "zones": [
            ("Side Stand", 500, 400),
            ("Grandstand", 1000, 200),
            ("VIP Lounge", 2500, 50),
        ],
    },
    {
        "name": "BRIC Superbike Championship",
        "category": "มอเตอร์ไซค์",
        "race_date": "29/08/2026",
        "venue": _VENUE,
        "price_from": 400,
        "zones": [
            ("Side Stand", 400, 400),
            ("Grandstand", 800, 200),
            ("VIP Lounge", 2000, 50),
        ],
    },
    {
        "name": "Thailand Grand Prix Endurance",
        "category": "รถยนต์ทางเรียบ (Endurance)",
        "race_date": "12/09/2026",
        "venue": _VENUE,
        "price_from": 600,
        "zones": [
            ("Side Stand", 600, 400),
            ("Grandstand", 1200, 200),
            ("VIP Lounge", 3000, 50),
        ],
    },
]


def seed_if_empty() -> None:
    with Session(engine) as db:
        if db.exec(select(Race)).first():
            return

        for item in _SAMPLE_RACES:
            race = Race(
                name=item["name"],
                category=item["category"],
                race_date=item["race_date"],
                venue=item["venue"],
                price_from=item["price_from"],
            )
            db.add(race)
            db.flush()  # ให้ได้ race.id ก่อนสร้างโซน

            for zone_name, price, seats in item["zones"]:
                db.add(
                    Zone(
                        race_id=race.id,
                        name=zone_name,
                        price=price,
                        total_seats=seats,
                        available_seats=seats,
                    )
                )

        db.commit()
        print(f"[Seed] Inserted {len(_SAMPLE_RACES)} races.")
