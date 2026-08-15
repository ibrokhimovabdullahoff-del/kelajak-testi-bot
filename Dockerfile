FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite fayli konteyner qayta ishga tushganda yo'qolmasligi uchun /data ga
# doimiy disk ulanadi (Railway'da volume, mount path: /data).
# VOLUME ko'rsatmasi ataylab yozilmagan — Railway diskni o'zi ulaydi va
# ikkalasi bir-biriga xalaqit berishi mumkin. mkdir esa disk ulanmay qolgan
# holatda ham yo'l mavjud bo'lishini kafolatlaydi.
RUN mkdir -p /data
ENV DB_PATH=/data/kelajak.db

CMD ["python", "main.py"]
