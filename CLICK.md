# 💳 Click integratsiyasi — nima qilingan va endi nima qilish kerak

Bot endi **pullik**: test faqat to'lov Click tomonidan **tasdiqlangandan
keyin** ochiladi. Boshqa to'lov usuli yo'q.

---

## 1. Qanday ishlaydi

```
Odam testni tanlaydi
        │
        ▼
  🔒 Paywall: narx ko'rsatiladi
        │  «Click orqali to'lash»
        ▼
  Bazada buyurtma ochiladi  ──►  merchant_trans_id = buyurtma raqami
        │
        ▼
  my.click.uz havolasi  ──►  odam karta yoki Click Up bilan to'laydi
        │
        ▼
  Click BIZGA murojaat qiladi:
        1) POST /click/prepare    «buyurtma bormi, summa to'g'rimi?»
        2) POST /click/complete   «pul yechildi, xizmatni bering»
        │
        ▼
  Faqat SHU yerda huquq beriladi  ──►  botda «✅ To'lov qabul qilindi»
```

Muhim: huquq **faqat** `/click/complete` so'rovi kelganda beriladi. Botdagi
«To'ladim» tugmasi ham o'zicha hech narsa ochmaydi — u Click API'dan
holatni so'raydi va faqat Click «to'landi» desa ochadi. Ya'ni to'lamay
turib testga kirishning yo'li yo'q.

---

## 2. Qaysi metod tanlandi

Click bergan uchta variantdan **3-si** (to'lov havolasi / tugmasi) asosiy
qilib olindi, chunki u hammaga ishlaydi: Click Up o'rnatilgan bo'lsa ilova
ochiladi, bo'lmasa `my.click.uz` sahifasida karta bilan to'lanadi.

**2-metod (invoice → Click Up push)** ham yozib qo'yilgan, lekin `.env` da
`CLICK_INVOICE=0` bilan o'chirilgan. Click bu metodni xizmatingizga yoqib
bergandan keyin `CLICK_INVOICE=1` qilsangiz, to'lov ekranida «📲 Click Up
ilovamga yuborish» tugmasi paydo bo'ladi.

**1-metod (Telegram Payments API)** olinmadi: unda odam karta raqami va
amal qilish muddatini Telegram oynasiga kiritishi kerak — bu ishonchni
pasaytiradi va konversiyani tushiradi.

---

## 3. Siz bajaradigan qadamlar

### 3.1. Deploy qiling va domenni oling

Bot endi **web-servis** (avval `worker` edi) — chunki Click bizga so'rov
yuborishi kerak, demak tashqaridan ochiq manzil shart.

Railway'da:

1. Loyihani odatdagidek deploy qiling.
2. **Settings → Networking → Generate Domain** bosing.
3. Chiqqan manzilni nusxalang, masalan `https://kelajak-bot.up.railway.app`.

Tekshirish:

```bash
curl https://SIZNING-DOMEN/health
```

`{"status": "ok"}` chiqishi kerak.

### 3.2. Muhit o'zgaruvchilarini to'ldiring

Railway → **Variables** bo'limiga quyidagilarni qo'shing:

| Nom | Qiymat |
|---|---|
| `CLICK_SERVICE_ID` | `110965` |
| `CLICK_MERCHANT_ID` | `64192` |
| `CLICK_SECRET_KEY` | *(Click bergan maxfiy kalit)* |
| `CLICK_MERCHANT_USER_ID` | `90473` |
| `PUBLIC_URL` | `https://kelajak-bot.up.railway.app` |
| `PRICE_UZS` | bitta test narxi, masalan `9900` |
| `PRICE_ALL_UZS` | «barcha testlar» paketi, masalan `24900` |

`PUBLIC_URL` oxirida `/` bo'lmasin.

> ⚠️ Maxfiy kalit chatda ochiq yozilgan edi. Xavfsizlik uchun Click'dan
> uni yangilashni so'rab qo'yish ma'qul — kalit almashsa, faqat shu
> o'zgaruvchini yangilaysiz, kodga tegish shart emas.

### 3.3. merchant.click.uz kabinetida manzillarni yozing

1. [merchant.click.uz](https://merchant.click.uz) ga kiring
2. Chapdagi **«Сервисы»** bo'limi
3. Jadvalning eng o'ng katagi — **«Действие»** ustunidagi ✏️ qalam belgisi
4. Quyidagilarni yozing:

| Maydon | Qiymat |
|---|---|
| Prepare URL (адрес проверки) | `https://SIZNING-DOMEN/click/prepare` |
| Complete URL (адрес результата) | `https://SIZNING-DOMEN/click/complete` |
| Return URL | `https://SIZNING-DOMEN/click/return` |

### 3.4. Click'ning test dasturidan o'tkazing

[docs.click.uz/click-api-testing](https://docs.click.uz/click-api-testing)
dagi vosita bilan integratsiyani tekshiring. Bizning tomondan hamma xato
kodlari hujjatdagidek qaytariladi:

| Kod | Qachon |
|---|---|
| `0` | hammasi joyida |
| `-1` | imzo mos kelmadi |
| `-2` | summa noto'g'ri |
| `-4` | allaqachon to'langan |
| `-5` | bunday buyurtma yo'q |
| `-6` | tranzaksiya topilmadi |
| `-8` | so'rov buzuq |
| `-9` | to'lov bekor qilingan |

### 3.5. Click'ga xabar bering va servisni yoqtiring

Testdan o'tgach, **birinchi haqiqiy to'lovdan OLDIN** Click guruhiga
quyidagi xabarni yuboring (tayyor matn — nusxalab yuboravering):

```
Здравствуйте!

Service ID: 110965
Merchant ID: 64192
Merchant User ID: 90473

Интеграция выполнена по SHOP API (docs.click.uz/shop-api/requests).
Планируем использовать метод №3 — оплата по ссылке/кнопке с переходом
в Click Up или на my.click.uz. В перспективе также метод №2 (создание
инвойса) — просим включить его для нашего сервиса.

Прописанные адреса:
  Prepare URL:  https://ВАШ-ДОМЕН/click/prepare
  Complete URL: https://ВАШ-ДОМЕН/click/complete
  Return URL:   https://ВАШ-ДОМЕН/click/return

Сервер находится ВНЕ сети TAS-IX. Просим добавить в белый список
файрвола:
  Домен: ВАШ-ДОМЕН
  IP:    ВАШ-IP
  Порт:  443

Тесты в ПО для тестирования пройдены. Просим активировать сервис.

У нас одно ИКПУ, поэтому метод фискализации чеков не подключаем.
Если это неверно — подскажите, пожалуйста.
```

`ВАШ-ДОМЕН` va `ВАШ-IP` ni o'zingiznikiga almashtiring. IP ni bilish uchun:

```bash
dig +short SIZNING-DOMEN
```

> ⚠️ **Statik IP haqida.** Click IP ning o'zgarmasligini talab qiladi.
> Railway'ning umumiy IP'lari o'zgarib turishi mumkin. Agar Click IP
> bo'yicha cheklov qo'ysa, ikki yo'l bor: (a) Railway'da statik chiqish
> IP'si bor tarifga o'tish, (b) O'zbekistondagi statik IP'li VPS'ga
> ko'chirish. Domen o'zgarmagani uchun kodga tegish shart emas — faqat
> `PUBLIC_URL` ni yangilaysiz.

### 3.6. Fiskalizatsiya

Click yozganidek: **1 tadan ortiq IKPU** ishlatsangiz, chek
fiskalizatsiyasi majburiy. Bizda mahsulot bir xil turdagi (psixologik test
xizmati) — bitta IKPU yetadi, shuning uchun fiskalizatsiya ulanmagan.
Buni Click bilan yozma tasdiqlab oling.

---

## 4. Botni boshqarish

`/admin` → **💳 To'lovlar**:

| Bo'lim | Nima qiladi |
|---|---|
| 🧾 Oxirgi to'lovlar | kim, qachon, qancha to'ladi |
| 💰 Narxlarni o'zgartirish | har bir test va paket narxi (deploy qilmasdan) |
| 🎁 Pullik / bepul testlar | bitta testni bepul qilib qo'yish (reklama uchun) |
| 🔓 Qo'lda ochish | pul boshqa yo'l bilan kelgan bo'lsa, huquqni qo'lda berish |

Adminlar hech qachon to'lov so'ralmaydi — panelni sinab ko'rish uchun pul
to'lash shart emas.

---

## 5. Tekshirish

```bash
./venv/bin/python clicktest.py
```

Bu skript haqiqiy Click serveriga ulanmaydi — o'zi Click bo'lib, hujjatdagi
formula bo'yicha imzo yasab, o'z serverimizga so'rov yuboradi. Tekshiriladi:
imzo, soxta imzo, noto'g'ri summa, yo'q buyurtma, takroriy Complete, bekor
qilingan to'lov.

Butun bot oqimi (paywall ham) uchun:

```bash
./venv/bin/python flowtest.py
```

---

## 6. Tez-tez uchraydigan muammolar

| Belgi | Sabab |
|---|---|
| Botda «To'lov tizimi ishlamayapti» | `PUBLIC_URL` yoki `CLICK_*` bo'sh — logda ogohlantirish chiqadi |
| Click «SIGN CHECK FAILED» deydi | `CLICK_SECRET_KEY` noto'g'ri yoki bo'sh joy bilan yozilgan |
| Pul yechildi, test ochilmadi | Click Complete so'rovi yetib kelmagan — logni qarang; odam «To'ladim» tugmasini bossa, Click API'dan tekshiriladi |
| Click «-2 Incorrect amount» | kabinetdagi narx bilan `PRICE_UZS` mos emas |
| Railway'da domen yo'q | servis `worker` bo'lib qolgan — `Procfile` da `web:` turishi kerak |
