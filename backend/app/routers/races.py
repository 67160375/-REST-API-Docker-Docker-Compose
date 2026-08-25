"""
routers/races.py
------------------
Endpoint ที่เกี่ยวกับ "รายการแข่งขัน" และ "โซนที่นั่ง"
ตรงกับขั้นตอนที่ 1-3 ในตาราง User Journey:
    1. ค้นหารายการแข่ง        (/races)
    2. ดูรายละเอียด&รอบแข่ง    (/race-detail)
    3. เลือกโซน & จำนวนตั๋ว    (/select-zone)
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from app import crud
from app.schemas import RaceSummary, RaceDetail, ZoneOut

router = APIRouter(prefix="/api/races", tags=["races"])


@router.get("", response_model=List[RaceSummary])
def get_races(keyword: Optional[str] = Query(default=None, description="คำค้นหาชื่อ/ประเภทการแข่งขัน")):
    """GET /api/races — รายการแข่งขันทั้งหมด (รองรับค้นหาด้วย keyword)"""
    return crud.list_races(keyword)


@router.get("/{race_id}", response_model=RaceDetail)
def get_race_detail(race_id: int):
    """GET /api/races/{race_id} — รายละเอียดการแข่งขัน 1 รายการ พร้อมกำหนดการกิจกรรม"""
    race = crud.get_race(race_id)
    if not race:
        raise HTTPException(status_code=404, detail="ไม่พบรายการแข่งขันนี้")
    return race


@router.get("/{race_id}/zones", response_model=List[ZoneOut])
def get_race_zones(race_id: int):
    """GET /api/races/{race_id}/zones — โซนที่นั่งทั้งหมดของรายการแข่งขันนี้ พร้อมที่นั่งคงเหลือ"""
    race = crud.get_race(race_id)
    if not race:
        raise HTTPException(status_code=404, detail="ไม่พบรายการแข่งขันนี้")
    return crud.list_zones(race_id)
