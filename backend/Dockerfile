# ---------------------------------------------------
# Dockerfile สำหรับ backend (FastAPI)
# ---------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# ติดตั้ง dependencies ก่อน เพื่อให้ Docker cache layer นี้ไว้
# (ถ้าโค้ดเปลี่ยนแต่ requirements ไม่เปลี่ยน จะไม่ต้อง pip install ใหม่ทุกครั้ง)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ด backend ทั้งหมดเข้า image
COPY ./app ./app

# เปิดพอร์ตที่ FastAPI/uvicorn ใช้งาน
EXPOSE 8000

# รันแอปด้วย uvicorn (--reload ใช้ตอน dev เท่านั้น ตอน production ควรถอดออก)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
