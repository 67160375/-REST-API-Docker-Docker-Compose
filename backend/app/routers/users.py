from fastapi import APIRouter

# ตั้งค่า Prefix สำหรับ API หมวด User Management
router = APIRouter(prefix="/api/v1/users", tags=["User Management"])

@router.get("/me")
def get_current_user():
    """ดึงข้อมูลโปรไฟล์ของตัวเอง"""
    return {
        "id": 1, 
        "username": "demo_user", 
        "email": "demo@example.com",
        "role": "customer"
    }

@router.get("/check-username/{name}")
def check_username(name: str):
    """ตรวจสอบ username ว่างไหม"""
    # จำลองว่าถ้าพิมพ์ชื่อ admin จะซ้ำ นอกนั้นว่าง
    is_available = name.lower() != "admin"
    return {"username": name, "available": is_available}

@router.get("/")
def get_all_users(skip: int = 0, limit: int = 10):
    """ดึงข้อมูล user ทั้งหมด (pagination)"""
    return [
        {"id": 1, "username": "demo_user", "email": "demo@example.com"},
        {"id": 2, "username": "admin", "email": "admin@example.com"}
    ]

@router.get("/{id}")
def get_user_by_id(id: int):
    """ดึงข้อมูล user ตาม ID"""
    return {"id": id, "username": f"user_{id}", "email": f"user_{id}@example.com"}

@router.put("/{id}")
def update_user(id: int, data: dict):
    """แก้ไขข้อมูล user"""
    return {"id": id, "message": "อัปเดตข้อมูลผู้ใช้งานสำเร็จ", "updated_data": data}

@router.delete("/{id}")
def delete_user(id: int):
    """ลบ user"""
    return {"id": id, "message": "ลบผู้ใช้งานสำเร็จ"}