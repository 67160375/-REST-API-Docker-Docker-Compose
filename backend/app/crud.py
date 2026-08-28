"""
crud.py
--------
รอบนี้ (สัปดาห์ 1) ยังไม่เชื่อมฐานข้อมูลจริง จึงใช้ "mock data" เก็บในตัวแปร
Python ธรรมดา (list ของ dict) จำลองการทำงานของฐานข้อมูลไปก่อน

ทุกฟังก์ชันตั้งชื่อและ signature ให้ใกล้เคียงกับของจริงที่จะใช้ SQLModel
session ในสัปดาห์ที่ 2 (ดู database.py + models.py) เพื่อให้ตอนสลับไปใช้
ฐานข้อมูลจริง แก้เฉพาะเนื้อหาข้างในฟังก์ชัน ไม่ต้องแก้ที่ router เรียกใช้งาน
"""

from typing import Optional
import copy
import itertools

# ---------------------------------------------------------------
# Mock data: รายการแข่งขัน
# หมายเหตุ: "price_from" ที่พิมพ์ไว้ตรงนี้เป็นแค่ค่าเริ่มต้น/placeholder เท่านั้น
# ตัวเลขจริงที่ส่งออกไปให้ frontend จะถูกคำนวณใหม่เสมอจากราคาต่ำสุดใน ZONES
# (ดูฟังก์ชัน get_price_from ด้านล่าง) เพื่อไม่ให้ราคาไม่ตรงกันอีก
# ---------------------------------------------------------------
RACES = [
    {
        "id": 1,
        "name": "Thailand Super Series 2026",
        "category": "รถยนต์ทางเรียบ",
        "race_date": "15/08/2026",
        "venue": "ช้าง อินเตอร์เนชั่นแนล เซอร์กิต จ.บุรีรัมย์",
        "price_from": 500,
        "image_url": "/assets/race-1.svg",
        "description": "การแข่งขันรถยนต์ทางเรียบรายการใหญ่ที่สุดของไทย ชมความเร็วระดับซูเปอร์คาร์ พร้อมกิจกรรม Pit Walk และพบนักแข่งตัวจริง",
        "venue_map_url": "/assets/venue-map-1.svg",
        "activities": [
            {"time": "08:00", "title": "เปิดประตูสนาม / เช็คอิน"},
            {"time": "10:00", "title": "Pit Walk พบทีมแข่ง"},
            {"time": "13:00", "title": "รอบคัดเลือก (Qualifying)"},
            {"time": "15:30", "title": "การแข่งขันหลัก (Main Race)"},
        ],
    },
    {
        "id": 2,
        "name": "BRIC Superbike Championship",
        "category": "มอเตอร์ไซค์",
        "race_date": "29/08/2026",
        "venue": "สนามช้าง อินเตอร์เนชั่นแนล เซอร์กิต จ.บุรีรัมย์",
        "price_from": 400,
        "image_url": "/assets/race-2.svg",
        "description": "ศึกความเร็วบนสองล้อระดับประเทศ พร้อมโชว์สตันต์ก่อนเริ่มการแข่งขันจริง",
        "venue_map_url": "/assets/venue-map-1.svg",
        "activities": [
            {"time": "09:00", "title": "เปิดประตูสนาม"},
            {"time": "11:00", "title": "โชว์สตันต์มอเตอร์ไซค์"},
            {"time": "14:00", "title": "การแข่งขันหลัก"},
        ],
    },
    {
        "id": 3,
        "name": "Thailand Grand Prix Endurance",
        "category": "รถยนต์ทางเรียบ (Endurance)",
        "race_date": "12/09/2026",
        "venue": "สนามช้าง อินเตอร์เนชั่นแนล เซอร์กิต จ.บุรีรัมย์",
        "price_from": 600,
        "image_url": "/assets/race-3.svg",
        "description": "การแข่งขันความอึด 6 ชั่วโมง ชมทีมแข่งสลับนักขับกลางสนามแบบใกล้ชิด",
        "venue_map_url": "/assets/venue-map-1.svg",
        "activities": [
            {"time": "07:30", "title": "เปิดประตูสนาม"},
            {"time": "09:00", "title": "ปล่อยตัว (Start)"},
            {"time": "15:00", "title": "เข้าเส้นชัย (Finish)"},
        ],
    },
]

# ---------------------------------------------------------------
# Mock data: โซนที่นั่งต่อรายการแข่งขัน
# ---------------------------------------------------------------
ZONES = [
    {"id": 1, "race_id": 1, "name": "Side Stand", "price": 500, "total_seats": 200, "available_seats": 42},
    {"id": 2, "race_id": 1, "name": "Grandstand", "price": 1500, "total_seats": 300, "available_seats": 150},
    {"id": 3, "race_id": 1, "name": "VIP", "price": 3500, "total_seats": 50, "available_seats": 20},
    {"id": 4, "race_id": 2, "name": "Side Stand", "price": 400, "total_seats": 200, "available_seats": 88},
    {"id": 5, "race_id": 2, "name": "Grandstand", "price": 1200, "total_seats": 300, "available_seats": 210},
    {"id": 6, "race_id": 2, "name": "VIP", "price": 3000, "total_seats": 40, "available_seats": 20},
    {"id": 7, "race_id": 3, "name": "Side Stand", "price": 600, "total_seats": 200, "available_seats": 120},
    {"id": 8, "race_id": 3, "name": "Grandstand", "price": 1800, "total_seats": 300, "available_seats": 260},
    {"id": 9, "race_id": 3, "name": "VIP", "price": 4000, "total_seats": 30, "available_seats": 20},
]

# ---------------------------------------------------------------
# Mock data: การจอง / ตั๋ว (เก็บใน memory เท่านั้น จะหายเมื่อรีสตาร์ทเซิร์ฟเวอร์
# — ปกติของ mock data สัปดาห์ 1 พอสัปดาห์ 2 ค่อยย้ายไป PostgreSQL จริง)
# ---------------------------------------------------------------
BOOKINGS: dict[int, dict] = {}
TICKETS: dict[int, dict] = {}
_booking_id_counter = itertools.count(1)

# เก็บค่าตั้งต้นของ ZONES ไว้ตอนโปรแกรมเริ่มทำงาน ใช้ตอนกด "รีเซ็ต" (ดู reset_all_data ด้านล่าง)
_ZONES_SEED = copy.deepcopy(ZONES)


# ---------------------------------------------------------------
# 🆕 ราคาเริ่มต้น: คำนวณจากราคาต่ำสุดในโซนของ race นั้นเสมอ
# ไม่ใช้ค่า "price_from" ที่พิมพ์ไว้ตรงๆ ใน RACES อีกต่อไป กัน "ราคาเริ่มต้น" กับ
# "ราคาโซนจริง" ไม่ตรงกันเวลามีคนแก้ราคาโซนแล้วลืมไปแก้ RACES
# ---------------------------------------------------------------
def get_price_from(race_id: int):
    zone_prices = [z["price"] for z in ZONES if z["race_id"] == race_id]
    return min(zone_prices) if zone_prices else None


def list_races(keyword: Optional[str] = None):
    races = RACES
    if keyword:
        keyword = keyword.strip().lower()
        races = [r for r in RACES if keyword in r["name"].lower() or keyword in r["category"].lower()]

    result = []
    for r in races:
        race_copy = dict(r)
        computed_price = get_price_from(r["id"])
        if computed_price is not None:
            race_copy["price_from"] = computed_price
        result.append(race_copy)
    return result


def get_race(race_id: int):
    race = next((r for r in RACES if r["id"] == race_id), None)
    if not race:
        return None
    race_copy = dict(race)
    computed_price = get_price_from(race_id)
    if computed_price is not None:
        race_copy["price_from"] = computed_price
    return race_copy


def list_zones(race_id: int):
    return [z for z in ZONES if z["race_id"] == race_id]


def get_zone(zone_id: int):
    return next((z for z in ZONES if z["id"] == zone_id), None)


def create_booking(race_id: int, zone_id: int, quantity: int):
    """ล็อกที่นั่งชั่วคราว (mock) แล้วสร้างการจองสถานะ pending"""
    zone = get_zone(zone_id)
    if not zone or zone["available_seats"] < quantity:
        return None

    zone["available_seats"] -= quantity  # จำลองการล็อกที่นั่งชั่วคราว

    booking_id = next(_booking_id_counter)
    booking = {
        "id": booking_id,
        "race_id": race_id,
        "zone_id": zone_id,
        "quantity": quantity,
        "buyer_name": None,
        "buyer_phone": None,
        "payment_method": None,
        "total_price": zone["price"] * quantity,
        "status": "pending",
    }
    BOOKINGS[booking_id] = booking
    return booking


def get_booking(booking_id: int):
    return BOOKINGS.get(booking_id)


def update_checkout_info(booking_id: int, buyer_name: str, buyer_phone: str, payment_method: str):
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return None
    booking["buyer_name"] = buyer_name
    booking["buyer_phone"] = buyer_phone
    booking["payment_method"] = payment_method
    booking["status"] = "awaiting_payment"
    return booking


def confirm_payment(booking_id: int, payment_method: str):
    booking = BOOKINGS.get(booking_id)
    if not booking:
        return None
    booking["payment_method"] = payment_method
    booking["status"] = "paid"

    ticket_code = f"TIX-{booking_id:06d}"
    ticket = {
        "booking_id": booking_id,
        "ticket_code": ticket_code,
        "qr_code_data": f"race-ticket-thailand://verify/{ticket_code}",
    }
    TICKETS[booking_id] = ticket
    return ticket


def get_ticket(booking_id: int):
    return TICKETS.get(booking_id)


# ---------------------------------------------------------------
# 🆕 รีเซ็ตข้อมูล (ใช้ตอนทดสอบเท่านั้น) -- เรียกผ่าน POST /api/dev/reset
# ---------------------------------------------------------------
def reset_all_data():
    """รีเซ็ตที่นั่งคงเหลือกลับเป็นค่าตั้งต้น + ล้างการจอง/ตั๋วทั้งหมด"""
    for zone in ZONES:
        seed = next(z for z in _ZONES_SEED if z["id"] == zone["id"])
        zone["available_seats"] = seed["available_seats"]
    BOOKINGS.clear()
    TICKETS.clear()