"""
slip_verify.py
---------------
ตรวจสลิปโอนเงินอัตโนมัติผ่านบริการภายนอก (ไม่บังคับ เปิดด้วย SLIP_VERIFY_PROVIDER ใน .env)

หลักการ: ระบบนี้ "ช่วยอนุมัติ" เท่านั้น
  - ผ่านทุกเงื่อนไข  -> อนุมัติ + ออกตั๋วทันที
  - ไม่ผ่าน / ระบบภายนอกล่ม / โควตาหมด / อ่านผลไม่ออก -> ส่งเข้าคิวให้แอดมินตรวจตามปกติ
ไม่มีกรณีที่ระบบอัตโนมัติ "ปฏิเสธ" ลูกค้าเอง เพื่อไม่ให้ลูกค้าที่จ่ายจริงเสียสิทธิ์เพราะ API ผิดพลาด

⚠️ ตัวเชื่อม EasySlip เขียนตามรูปแบบ API ที่เผยแพร่ แต่ยังไม่ได้ทดสอบกับบัญชีจริง
   ก่อนเปิดใช้ ให้ทดสอบด้วยการโอนจริงยอดเล็กๆ แล้วดูผลในช่อง verify_note ของหน้าแอดมิน
"""

import json
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app import config


@dataclass
class VerifyResult:
    approved: bool  # True = ผ่านครบ อนุมัติอัตโนมัติได้
    note: str  # ข้อความสรุปผลให้แอดมินอ่าน
    ref: Optional[str] = None  # เลขอ้างอิงรายการโอน (กันสลิปเดิมใช้ซ้ำ)


def is_enabled() -> bool:
    return config.SLIP_VERIFY_PROVIDER not in ("", "none") and bool(config.SLIP_VERIFY_API_KEY)


def verify_slip(
    image: bytes,
    filename: str,
    content_type: str,
    expected_amount: float,
    booking_created_at: datetime,
    ref_already_used,  # callable(ref: str) -> bool
) -> Optional[VerifyResult]:
    """คืน None ถ้าไม่ได้เปิดใช้ระบบตรวจอัตโนมัติ"""
    if not is_enabled():
        return None
    if config.SLIP_VERIFY_PROVIDER == "easyslip":
        try:
            data = _call_easyslip(image, filename, content_type)
        except Exception as e:  # noqa: BLE001 - ระบบภายนอกล้มเหลว -> ให้แอดมินตรวจ
            return VerifyResult(False, f"ตรวจอัตโนมัติไม่สำเร็จ ({type(e).__name__}: {str(e)[:150]})")
        return _check(data, expected_amount, booking_created_at, ref_already_used)
    return VerifyResult(False, f"ไม่รู้จักผู้ให้บริการตรวจสลิป '{config.SLIP_VERIFY_PROVIDER}'")


# ---------------------------------------------------------------
# EasySlip
# ---------------------------------------------------------------
def _call_easyslip(image: bytes, filename: str, content_type: str) -> dict:
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + image + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        config.SLIP_VERIFY_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {config.SLIP_VERIFY_API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        raise RuntimeError(f"HTTP {e.code}: {detail}") from None

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise RuntimeError(f"รูปแบบผลตอบกลับไม่รู้จัก: {str(payload)[:200]}")
    return data


def _num(v: Any) -> Optional[float]:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict):
        return _num(v.get("amount"))
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _strings(obj: Any) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _strings(v)]
    return []


def _parse_dt(v: Any) -> Optional[datetime]:
    if not isinstance(v, str):
        return None
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:  # ไม่ระบุโซน ถือว่าเวลาไทย
        dt = dt.replace(tzinfo=timezone(timedelta(hours=7)))
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _check(data: dict, expected_amount: float, created_at: datetime, ref_already_used) -> VerifyResult:
    problems = []

    amount = _num(data.get("amount"))
    if amount is None:
        problems.append("อ่านยอดเงินไม่ได้")
    elif abs(amount - expected_amount) > 0.001:
        problems.append(f"ยอดไม่ตรง (สลิป {amount:,.2f} / ต้องได้ {expected_amount:,.2f})")

    ref = data.get("transRef") or data.get("reference")
    if not ref:
        problems.append("ไม่มีเลขอ้างอิงรายการ")
    elif ref_already_used(str(ref)):
        problems.append(f"เลขอ้างอิง {ref} เคยใช้กับการจองอื่นแล้ว")

    paid_at = _parse_dt(data.get("date") or data.get("transactionDate"))
    if paid_at is None:
        problems.append("อ่านเวลาโอนไม่ได้")
    elif paid_at < created_at - timedelta(minutes=5):
        problems.append("เวลาโอนก่อนเวลาที่สร้างการจอง")

    if config.SLIP_RECEIVER_HINT:
        receiver_text = " ".join(_strings(data.get("receiver"))).lower()
        if config.SLIP_RECEIVER_HINT.lower() not in receiver_text:
            problems.append("ผู้รับเงินไม่ตรงกับบัญชีร้าน")

    if problems:
        return VerifyResult(False, "ตรวจอัตโนมัติไม่ผ่าน: " + "; ".join(problems), str(ref) if ref else None)
    return VerifyResult(True, f"ตรวจอัตโนมัติผ่าน (ref {ref})", str(ref))
