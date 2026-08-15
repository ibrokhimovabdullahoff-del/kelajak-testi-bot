# 🧠 Psixologik testlar boti — [@kelajak_testi_bot](https://t.me/kelajak_testi_bot)

O‘zbek va rus tilidagi Telegram bot: to‘rtta psixologik test, har birining
ilmiy manbasi ochiq ko‘rsatilgan.

| Test | Savollar | Turi | Manba |
|---|---|---|---|
| 🧠 Big Five — shaxsiyat profili | 50 | profil (umumiy ballsiz) | **IPIP Big-Five Factor Markers**, Goldberg 1992 — validatsiyalangan |
| 🎯 Kelajak salohiyati | 28 | 0–100 indeks | mualliflik so‘rovnomasi |
| 🧭 Kasb yo‘nalishi (RIASEC) | 30 | Holland kodi | Holland modeli, savollar bizniki |
| 👶 Farzand salohiyati | 24 | 0–100 indeks | mualliflik so‘rovnomasi |

---

## Eng muhim qaror: nima validatsiyalangan, nima yo‘q

Bot har bir testda **ochiq aytib turadi**, u validatsiyadan o‘tgan asbobmi
yoki mualliflik so‘rovnomasi. Har bir test kartochkasida «📚 Manba» tugmasi
bor.

**Big Five** — [International Personality Item Pool](https://ipip.ori.org/)
dan olingan 50 elementli Big-Five Factor Markers. IPIP saytida aniq
yozilgan: elementlar **ochiq mulk (public domain)** — ruxsatsiz va to‘lovsiz
nusxalash, tarjima qilish va **tijorat maqsadida ishlatish** mumkin. Bu
model minglab tadqiqotlarda sinovdan o‘tgan.

**Qolgan uchtasi** — nashr etilgan ilmiy topilmalarga tayanadi (Duckworth,
Dweck, Moffitt/Dunedin, Rotter, Holland, Harvard Grant Study), lekin
so‘rovnomalarning o‘zi psixometrik validatsiyadan o‘tmagan.

> **Reklama uchun.** «IPIP Big-Five Factor Markers asosida» yoki «Goldberg
> (1992) modeli asosida» deyish — haqiqat. «Harvard yaratgan test» deyish —
> yolg‘on: Harvard Grant Study bu testni tuzmagan, u shunchaki
> munosabatlarning ahamiyatini ko‘rsatgan kuzatuv. Farqni saqlang: tekshirib
> ko‘rilganda birinchisi mustahkam turadi, ikkinchisi obro‘ni yo‘q qiladi.

Big Five natijasida **ataylab umumiy ball chiqarilmaydi** — Big Five odamni
«yaxshi/yomon»ga ajratmaydi. Umumiy ball chiqarish testni psixometrik
jihatdan noto‘g‘ri qilib qo‘yardi.

---

## Ikki til

Birinchi `/start` da til so‘raladi, tanlov bazada saqlanadi. Keyin hamma
narsa — menyu, savollar, natija, ogohlantirishlar — o‘sha tilda. `/til`
bilan istalgan vaqtda almashtiriladi.

Admin panel faqat o‘zbekcha (u faqat siz uchun).

---

## Ishga tushirish

```bash
cd ~/Desktop/kelajak-bot && ./venv/bin/python main.py
```

Nolgacha o‘rnatish:

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt && cp .env.example .env
```

---

## Tekshiruv

Har qanday o‘zgarishdan keyin uchalasini ishlating:

```bash
./venv/bin/python selftest.py && ./venv/bin/python flowtest.py && ./venv/bin/python migrationtest.py
```

**`selftest.py`** — 323 ta ikki tilli matnni tekshiradi:

- tarjima tushib qolganmi, bo‘sh matn bormi
- HTML teglar yopilganmi, begona alifbo belgilari kirib qolganmi
- **o‘zbekcha apostroflar to‘g‘rimi** (o‘/g‘ uchun bir belgi, tutuq belgisi
  uchun boshqasi)
- **kitobiy so‘zlar ishlatilmaganmi** — `BANNED_UZ` ro‘yxati: «izchil»,
  «bashoratchi», «kechinma», «o‘zgalar» kabi so‘zlar bot matnida bo‘lmasligi
  kerak, chunki oddiy odam ularni ishlatmaydi
- **natija juda uzun emasmi** — har bir daraja izohi 300 belgidan, butun
  natija 1900 belgidan oshmasligi kerak
- ball chegaralari: eng past javob 0, eng yuqorisi 100 berishi kerak

**`flowtest.py`** — 62 ta tekshiruv: butun bot oqimi soxta Telegram sessiyasi
bilan haqiqatan ishga tushiriladi — ikkala tilda test topshirish, «Orqaga»,
ikki marta bosish himoyasi, eski tugma, tarix, admin panel, oddiy
foydalanuvchining admin panelga kira olmasligi. **Hech kimga xabar
yubormaydi**, vaqtinchalik bazaga yozadi.

**`migrationtest.py`** — eski bazadan ko‘chishni sinaydi va **ko‘chgandan
keyin yangi natija yozilishini** tekshiradi. Bu alohida skript, chunki
qolgan ikkitasi doim toza bazadan boshlaydi va eski sxemadagi muammoni
ko‘rmaydi. Aynan shu bo‘shliq tufayli `results.mode NOT NULL` xatosi ishlab
turgan botga chiqib ketgan edi.

---

## Fayllar

| Fayl | Nima qiladi |
|---|---|
| `main.py` | kirish nuqtasi, polling, buyruqlar ro‘yxati |
| `config.py` | `.env` dan sozlamalar |
| `locales.py` | interfeys matnlari, ikki tilda |
| `psytests/base.py` | test tuzilmasi va ball hisobi (matnsiz mexanika) |
| `psytests/bigfive.py` | IPIP-50 — **savollar shu yerda** |
| `psytests/future.py` | Kelajak salohiyati |
| `psytests/career.py` | RIASEC |
| `psytests/child.py` | Farzand salohiyati |
| `psytests/__init__.py` | reyestr, yosh guruhlari, yosh maslahatlari |
| `report.py` | natija matnini yig‘ish |
| `keyboards.py` | inline tugmalar |
| `database.py` | SQLite + eski bazadan avtomatik ko‘chirish |
| `handlers/middleware.py` | foydalanuvchi va tilni aniqlash |
| `handlers/user.py` | menyu, test oqimi, natija |
| `handlers/admin.py` | statistika va ommaviy xabar |

### Yangi test qo‘shish

1. `psytests/` da yangi fayl yarating, unda `TEST = TestDef(...)` e’lon qiling
2. Uni `psytests/__init__.py` dagi `REGISTRY` va `ORDER` ga qo‘shing
3. `selftest.py` ni ishlating

Menyu, ball hisobi, natija, tarix va statistika o‘zi moslashadi — boshqa
hech qayerni o‘zgartirish shart emas.

### Savol matnini o‘zgartirish

Faqat tegishli `psytests/*.py` faylini tahrirlang. Ikkala tilni ham yozing —
`selftest.py` biri tushib qolsa xato beradi.

---

## Admin panel

`/admin` (faqat `ADMIN_ID` uchun):

- 📊 **Statistika** — foydalanuvchilar, bugungi qo‘shilganlar, **til bo‘yicha
  bo‘linish**, har bir test bo‘yicha soni va o‘rtacha ball
- 📣 **Xabar yuborish** — hammaga, faqat o‘zbekchaga yoki faqat ruschaga.
  Tasdiqlash so‘raladi, bloklaganlar avtomatik belgilanadi

---

## Deploy (Railway)

`Dockerfile`, `Procfile` va `railway.json` tayyor. Muhit o‘zgaruvchilarini
Railway panelida qo‘ying, `.env` faylini serverga yuklamang:

```
BOT_TOKEN, ADMIN_ID, BOT_USERNAME, DB_PATH
```

**SQLite fayli uchun doimiy disk (volume) ulang** va `DB_PATH` ni o‘shanga
yo‘naltiring (`/data/kelajak.db`). Aks holda har qayta deployda barcha
foydalanuvchilar va natijalar o‘chib ketadi.

Baza sxemasi **avtomatik ko‘chadi**: eski `mode` ustuni `test_key` ga,
`adult` → `future`, `kid` → `child`. Eski natijalar yo‘qolmaydi.

**Bitta nusxa ishlasin.** Telegram bir tokenga ikkita polling ulanishiga
ruxsat bermaydi — Railway'ga chiqarganingizda lokal nusxani to‘xtating.

---

## Cheklovlar

- **Yarim yo‘ldagi testlar xotirada** (`MemoryStorage`). Bot qayta ishga
  tushsa, o‘sha paytda test topshirayotganlar boshidan boshlaydi. Tugallangan
  natijalar bazada — ular yo‘qolmaydi. Redis storage ga o‘tkazish ~10 daqiqalik
  ish.
- **Ommaviy xabar** ketma-ket ketadi (~20 xabar/sekund). 10 000 foydalanuvchida
  ~8 daqiqa.
- Python **3.14** da sinaldi (`venv/`), Dockerfile da 3.12.
