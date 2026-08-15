FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite fayli konteyner qayta ishga tushganda yo'qolmasligi uchun
# shu jildni volume qilib ulang.
ENV DB_PATH=/data/kelajak.db
VOLUME ["/data"]

CMD ["python", "main.py"]
