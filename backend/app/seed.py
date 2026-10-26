"""
seed.py
--------
ข้อมูลตัวอย่างตอนเริ่มระบบ (รันซ้ำกี่ครั้งก็ปลอดภัย)

seed_if_empty()      ตาราง Race ว่าง -> ใส่รายการแข่ง + โซน + ตารางเวลา
sync_sample_data()   DB ที่มีข้อมูลอยู่แล้ว -> เติมของใหม่ที่ยังไม่มี โดยไม่ลบ/ทับข้อมูลจริง
                     - รวมโซนซ้ำที่เกิดจากบั๊ก seed เดิม (ย้ายการจองที่ผูกอยู่มาด้วย)
                     - เติมภาพผังสนาม / ตำแหน่งโซนบนภาพ / ตารางเวลา ให้รายการที่ยังไม่มี
                     - เลื่อนวันแข่งของ "ข้อมูลตัวอย่างชุดเดิม" ที่ผ่านไปแล้ว

⚠️ ชื่อโซน ราคา จำนวนที่นั่ง ตารางเวลา และภาพผังสนาม เป็น "ค่าสมมติ" รอข้อมูลจริง
   ตอนได้ข้อมูลจริง แก้ในไฟล์นี้ หรือแก้ใน DB ผ่าน Adminer (http://localhost:8080)
"""

from collections import defaultdict

from sqlmodel import Session, select

from app.database import engine
from app.models import Booking, Race, ScheduleItem, Zone

_VENUE = "ช้าง อินเตอร์เนชั่นแนล เซอร์กิต จ.บุรีรัมย์"
DEFAULT_MAP_URL = "/assets/circuit-map.png"
_SEAT_TAKING_STATUSES = ("pending", "awaiting_payment", "pending_review", "rejected", "paid")

# ตำแหน่งโซนบนภาพผังสนาม (หน่วย % ของภาพ: x, y, กว้าง, สูง) ต้องตรงกับภาพที่ใช้
# เปลี่ยนภาพใหม่: เปิดหน้าเลือกโซนด้วย ?mapdebug=1 แล้วคลิกบนภาพเพื่อดูพิกัด %
ZONE_MAP_POSITIONS = {
    "Side Stand": (44.1, 9.6, 29.5, 8.0),
    "Grandstand": (5.0, 35.1, 13.0, 12.3),
    "VIP Lounge": (5.0, 49.0, 13.0, 9.8),
}

# จุดเด่นของแต่ละโซน (1 บรรทัด = 1 ข้อ) แสดงในหน้าเลือกโซน
ZONE_DESCRIPTIONS = {
    "VIP Lounge": "นั่งชั้นล่าง ต่ำกว่า Grandstand ใกล้สนามมากกว่า\nห้องรับรองติดแอร์\nได้ร่วมกิจกรรม Pit Walk",
}

# ค่าจากภาพผังสนาม "ชั่วคราว" ชุดก่อน — ใช้ตรวจว่า DB ยังเป็นค่าเก่าอยู่ไหม จะได้อัปเดตให้
_OLD_MAP_URLS = ("/assets/circuit-map.svg",)
_OLD_ZONE_MAP_POSITIONS = {
    "Side Stand": (88.0, 38.3, 7.0, 26.7),
    "Grandstand": (32.0, 81.7, 32.0, 11.7),
    "VIP Lounge": (66.0, 81.7, 12.0, 11.7),
}

# ตารางเวลา: (เริ่ม, จบ, ประเภทรถ/รุ่น, ชนิด, ชื่อรายการ)
_SCHEDULE_CARS = [
    ("08:00", None, "กิจกรรม", "activity", "ประตูเปิด / ลงทะเบียนเข้างาน"),
    ("08:30", "09:00", "Super Car GT3", "practice", "Free Practice"),
    ("09:10", "09:40", "Super Car GT3", "qualifying", "Qualifying"),
    ("09:50", "10:20", "Super Compact", "qualifying", "Qualifying"),
    ("10:30", "11:30", "กิจกรรม", "activity", "Pit Walk & แจกลายเซ็นนักแข่ง"),
    ("11:40", "12:10", "Super Compact", "race", "Race 1"),
    ("13:00", "13:40", "Super Car GT3", "race", "Race 1"),
    ("14:00", "14:30", "Thailand Touring Car", "race", "Race"),
    ("15:00", "15:40", "Super Car GT3", "race", "Race 2"),
    ("16:00", "16:30", "กิจกรรม", "activity", "พิธีมอบรางวัล"),
]
_SCHEDULE_BIKES = [
    ("08:00", None, "กิจกรรม", "activity", "ประตูเปิด / ลงทะเบียนเข้างาน"),
    ("08:30", "09:00", "Supersport 300", "practice", "Free Practice"),
    ("09:10", "09:50", "Superbike 1000cc", "qualifying", "Qualifying"),
    ("10:00", "10:30", "Supersport 600", "race", "Race 1"),
    ("10:45", "11:30", "กิจกรรม", "activity", "Pit Walk"),
    ("11:45", "12:25", "Superbike 1000cc", "race", "Race 1"),
    ("13:30", "14:00", "Supersport 600", "race", "Race 2"),
    ("14:30", "15:10", "Superbike 1000cc", "race", "Race 2"),
    ("15:30", "16:00", "กิจกรรม", "activity", "พิธีมอบรางวัล"),
]
_SCHEDULE_ENDURANCE = [
    ("07:30", None, "กิจกรรม", "activity", "ประตูเปิด / ลงทะเบียนเข้างาน"),
    ("08:00", "08:30", "Endurance GT", "practice", "Warm Up"),
    ("09:00", "09:45", "กิจกรรม", "activity", "Grid Walk ก่อนออกสตาร์ท"),
    ("10:00", "16:00", "Endurance GT", "race", "Endurance 6 Hours"),
    ("12:30", "13:00", "กิจกรรม", "activity", "ชมการเปลี่ยนนักขับใน Pit"),
    ("16:30", "17:00", "กิจกรรม", "activity", "พิธีมอบรางวัล"),
]

# โซนเป็น (ชื่อโซน, ราคา, จำนวนที่นั่ง) — ราคาโซนถูกสุดต้องเท่ากับ price_from
_SAMPLE_RACES = [
    {
        "name": "Thailand Super Series 2026",
        "category": "รถยนต์ทางเรียบ",
        "race_date": "28/11/2026",
        "old_date": "15/08/2026",
        "venue": _VENUE,
        "price_from": 500,
        "zones": [("Side Stand", 500, 400), ("Grandstand", 1000, 200), ("VIP Lounge", 2500, 50)],
        "schedule": _SCHEDULE_CARS,
    },
    {
        "name": "BRIC Superbike Championship",
        "category": "มอเตอร์ไซค์",
        "race_date": "12/12/2026",
        "old_date": "29/08/2026",
        "venue": _VENUE,
        "price_from": 400,
        "zones": [("Side Stand", 400, 400), ("Grandstand", 800, 200), ("VIP Lounge", 2000, 50)],
        "schedule": _SCHEDULE_BIKES,
    },
    {
        "name": "Thailand Grand Prix Endurance",
        "category": "รถยนต์ทางเรียบ (Endurance)",
        "race_date": "16/01/2027",
        "old_date": "12/09/2026",
        "venue": _VENUE,
        "price_from": 600,
        "zones": [("Side Stand", 600, 400), ("Grandstand", 1200, 200), ("VIP Lounge", 3000, 50)],
        "schedule": _SCHEDULE_ENDURANCE,
    },
]


def _zone(race_id: int, name: str, price: int, seats: int) -> Zone:
    x, y, w, h = ZONE_MAP_POSITIONS.get(name, (None, None, None, None))
    return Zone(race_id=race_id, name=name, price=price, total_seats=seats, available_seats=seats,
                map_x=x, map_y=y, map_w=w, map_h=h, description=ZONE_DESCRIPTIONS.get(name))


def _add_schedule(db: Session, race_id: int, items) -> None:
    for start, end, category, session_type, title in items:
        db.add(ScheduleItem(race_id=race_id, start_time=start, end_time=end,
                            category=category, session_type=session_type, title=title))


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
                venue_map_url=DEFAULT_MAP_URL,
            )
            db.add(race)
            db.flush()  # ให้ได้ race.id ก่อนสร้างโซน
            for zone_name, price, seats in item["zones"]:
                db.add(_zone(race.id, zone_name, price, seats))
            _add_schedule(db, race.id, item["schedule"])
        db.commit()
        print(f"[Seed] Inserted {len(_SAMPLE_RACES)} races.")


def sync_sample_data() -> None:
    with Session(engine) as db:
        samples = {s["name"]: s for s in _SAMPLE_RACES}
        removed = 0

        for race in db.exec(select(Race)).all():
            sample = samples.get(race.name)

            # 1) รวมโซนชื่อซ้ำในรายการเดียวกัน (เก็บ id ต่ำสุด)
            #    การจองที่ผูกกับโซนซ้ำ ย้ายมาโซนที่เก็บไว้ และหักที่นั่งที่ยังถือ/ขายแล้วออกให้ถูกต้อง
            by_name = defaultdict(list)
            for z in db.exec(select(Zone).where(Zone.race_id == race.id).order_by(Zone.id)).all():
                by_name[z.name].append(z)
            for name, zones in by_name.items():
                keep = zones[0]
                for dup in zones[1:]:
                    for b in db.exec(select(Booking).where(Booking.zone_id == dup.id)).all():
                        b.zone_id = keep.id
                        if b.status in _SEAT_TAKING_STATUSES:
                            keep.available_seats = max(0, keep.available_seats - b.quantity)
                        db.add(b)
                    db.add(keep)
                    db.flush()
                    db.delete(dup)
                    removed += 1
                by_name[name] = [keep]

            # 2) ตำแหน่งโซนบนภาพ + จุดเด่นของโซน
            #    อัปเดตเฉพาะโซนที่ยังว่าง หรือยังเป็นค่าของภาพชั่วคราวชุดเก่า (ค่าที่แก้เองจะไม่ถูกทับ)
            for zones in by_name.values():
                for z in zones:
                    current = (z.map_x, z.map_y, z.map_w, z.map_h)
                    if z.name in ZONE_MAP_POSITIONS and (
                        z.map_x is None or current == _OLD_ZONE_MAP_POSITIONS.get(z.name)
                    ):
                        z.map_x, z.map_y, z.map_w, z.map_h = ZONE_MAP_POSITIONS[z.name]
                        db.add(z)
                    if not z.description and z.name in ZONE_DESCRIPTIONS:
                        z.description = ZONE_DESCRIPTIONS[z.name]
                        db.add(z)

            # 3) ภาพผังสนาม (ว่าง หรือยังเป็นภาพชั่วคราวชุดเก่า -> ภาพปัจจุบัน)
            if not race.venue_map_url or race.venue_map_url in _OLD_MAP_URLS:
                race.venue_map_url = DEFAULT_MAP_URL
                db.add(race)

            # 4) ตารางเวลา (เฉพาะรายการที่ยังไม่มีเลย)
            has_schedule = db.exec(select(ScheduleItem.id).where(ScheduleItem.race_id == race.id)).first()
            if not has_schedule:
                _add_schedule(db, race.id, sample["schedule"] if sample else _SCHEDULE_CARS)

            # 5) เลื่อนวันของข้อมูลตัวอย่างชุดเดิม (ตรงทั้งชื่อและวันเดิมเท่านั้น)
            if sample and race.race_date == sample["old_date"]:
                race.race_date = sample["race_date"]
                db.add(race)

        db.commit()
        if removed:
            print(f"[Seed] Merged {removed} duplicated zone(s).")
