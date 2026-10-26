FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY frontend ./frontend
# ไฟล์สลิปที่ลูกค้าอัปโหลด (docker-compose mount volume ทับไว้ ไม่หายตอน rebuild)
ENV UPLOAD_DIR=/app/uploads
RUN mkdir -p /app/uploads
EXPOSE 8000
# ตอน deploy จริงไม่ใช้ --reload (ตอน dev เปิด reload ใน docker-compose.yml แทน)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
