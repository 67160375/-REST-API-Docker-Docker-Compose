"""
routers/races.py
------------------
Endpoint ที่เกี่ยวกับ "รายการแข่งขัน", "ตารางเวลาในวันแข่ง" และ "โซนที่นั่ง"
    GET /api/races                    1. ค้นหารายการแข่ง
    GET /api/races/{id}               2. รายละเอียด + ตารางเวลา + ภาพผังสนาม
    GET /api/races/{id}/schedule         ตารางเวลาของรายการนี้
    GET /api/races/{id}/zones         3. โซนที่นั่ง + ที่นั่งคงเหลือ + ตำแหน่งบนภาพผังสนาม
    GET /api/schedule                    ตารางการแข่งทุกรายการ เรียงตามวันที่
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app import crud
from app.database import get_db
from app.models import Race
from app.schemas import RaceDetail, RaceSchedule, RaceSummary, ScheduleItemOut, ZoneOut

router = APIRouter(prefix="/api", tags=["races"])


def _race_or_404(db: Session, race_id: int) -> Race:
    race = crud.get_race(db=db, race_id=race_id)
    if not race:
        raise HTTPException(status_code=404, detail="ไม่พบรายการแข่งขันนี้")
    return race


def _schedule(db: Session, race_id: int) -> List[ScheduleItemOut]:
    return [ScheduleItemOut.model_validate(s, from_attributes=True) for s in crud.list_schedule(db, race_id)]


def _date_key(race: Race):
    try:
        return datetime.strptime(race.race_date, "%d/%m/%Y")
    except ValueError:
        return datetime.max


@router.get("/races", response_model=List[RaceSummary])
def get_races(
    keyword: Optional[str] = Query(default=None, description="คำค้นหาชื่อ/ประเภทการแข่งขัน"),
    db: Session = Depends(get_db),
):
    """รายการแข่งขันทั้งหมด (รองรับค้นหาด้วย keyword)"""
    return crud.list_races(db=db, keyword=keyword)


@router.get("/races/{race_id}", response_model=RaceDetail)
def get_race_detail(race_id: int, db: Session = Depends(get_db)):
    """รายละเอียดการแข่งขัน 1 รายการ พร้อมตารางเวลาในวันแข่ง"""
    race = _race_or_404(db, race_id)
    data = RaceDetail.model_validate(race, from_attributes=True)
    data.schedule = _schedule(db, race_id)
    return data


@router.get("/races/{race_id}/schedule", response_model=List[ScheduleItemOut])
def get_race_schedule(race_id: int, db: Session = Depends(get_db)):
    _race_or_404(db, race_id)
    return _schedule(db, race_id)


@router.get("/races/{race_id}/zones", response_model=List[ZoneOut])
def get_race_zones(race_id: int, db: Session = Depends(get_db)):
    """โซนที่นั่งทั้งหมดของรายการแข่งขันนี้ พร้อมที่นั่งคงเหลือ"""
    _race_or_404(db, race_id)
    return crud.list_zones(db=db, race_id=race_id)


@router.get("/schedule", response_model=List[RaceSchedule])
def get_all_schedules(db: Session = Depends(get_db)):
    """ตารางการแข่งของทุกรายการ (1 รายการ = 1 วัน) เรียงตามวันที่จัด"""
    result = []
    for race in sorted(crud.list_races(db), key=_date_key):
        item = RaceSchedule.model_validate(race, from_attributes=True)
        item.schedule = _schedule(db, race.id)
        result.append(item)
    return result
