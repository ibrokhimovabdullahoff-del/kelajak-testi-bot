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

# Click to'lov haqida BIZGA murojaat qiladi, shuning uchun bot yonida HTTP
# server ham ishlaydi. Railway PORT ni o'zi beradi; bu yerdagi qiymat faqat
# mahalliy ishga tushirish uchun.
ENV PORT=8080
EXPOSE 8080

CMD ["python", "main.py"]
