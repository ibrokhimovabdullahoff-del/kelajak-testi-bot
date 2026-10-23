# 🧠 Psixologik testlar boti — [@kelajak_testi_bot](https://t.me/kelajak_testi_bot)

O‘zbek va rus tilidagi Telegram bot: to‘rtta psixologik test va rasmli IQ
testi, har birining manbasi ochiq ko‘rsatilgan.

| Test | Savollar | Turi | Manba |
|---|---|---|---|
| 🧠 Big Five — shaxsiyat profili | 50 | profil (umumiy ballsiz) | **IPIP Big-Five Factor Markers**, Goldberg 1992 — validatsiyalangan |
| 🎯 Kelajak salohiyati | 28 | 0–100 indeks | mualliflik so‘rovnomasi |
| 🧭 Kasb yo‘nalishi (RIASEC) | 30 | Holland kodi | Holland modeli, savollar bizniki |
| 👶 Farzand salohiyati | 24 | 0–100 indeks | mualliflik so‘rovnomasi |
| 🧠 Premium IQ testi | 20 rasm | taxminiy IQ (yoshga qarab) | Raven matritsalari uslubidagi topshiriqlar |

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

## Javob variantlari

Savollar **savol shaklida** beriladi va javoblar o‘sha savolning fe‘lini
takrorlaydi. Bu psixolog mutaxassisning tanqidiga javob: mavhum
«to‘liq to‘g‘ri» shkalasini oddiy foydalanuvchi tushunmaydi.

```
Davra siz bilan jonlanadimi?
  1️⃣ Hech qachon jonlanmaydi
  2️⃣ Kamdan-kam jonlanadi
  3️⃣ Ba’zan jonlanadi
  4️⃣ Ko‘pincha jonlanadi
  5️⃣ Doim jonlanadi
```

O‘rtadagi variant **«Bilmayman» emas**: odam «bilmayman» deb emas, «ba’zan»
yoki «o‘rtacha» deb javob beradi. Soni so‘raladigan savollarda (ekran vaqti,
haftada necha marta sport) javoblar raqam bilan beriladi — `kind="custom"`.

Variantlar `psytests/base.py` dagi shablonlardan yig‘iladi
(`freq`, `deg`, `yesno`, `agree`, `interest`), har bir savol esa faqat o‘z
fe‘lining tasdiq va inkor shaklini beradi.

**Muhim:** ishlab turgan bot savollarni koddan emas, **bazadagi CMS
jadvalidan** o‘qiydi. Savol matnini o‘zgartirishdan oldin
`python content_cms.py snapshot` ni ishga tushiring, keyin savollarni
o‘zgartirib, `content_cms.py` dagi `CONTENT_VERSION` ni oshiring —
migratsiya admin tegmagan testlarni yangi matn bilan almashtiradi
(tahrirlanganlarini saqlab qoladi). Batafsil: [CMS.md](CMS.md).

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
./venv/bin/python selftest.py && ./venv/bin/python flowtest.py && \
  ./venv/bin/python migrationtest.py && ./venv/bin/python clicktest.py
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

**`iqtest.py`** — rasmli IQ testi: rasmlar va javoblar kaliti (A–D teng
taqsimlangan), to‘lov to‘sig‘i, yosh tanlash, rasm Telegram'ga bir marta
yuklanishi, ikki marta bosish, taxminiy IQ, **to‘g‘ri javoblar foydalanuvchiga
hech qayerda ko‘rinmasligi**, to‘xtatish va to‘lovdan keyin avtomatik boshlanish.

**`contenttest.py`** — CMS migratsiyasi: serverdagi eski bazaga yangi
savollar to‘g‘ri qo‘llanishi, admin tahriri saqlanishi va tugmalar hech
qachon chala («Ha,») chiqmasligi.

**`clicktest.py`** — Click integratsiyasi. Haqiqiy Click serveriga
ulanmaydi: skriptning o‘zi Click bo‘lib, hujjatdagi formula bo‘yicha imzo
yasaydi va o‘z serverimizga so‘rov yuboradi. Shu sababli internetsiz ham
ishlaydi. Tekshiriladi: imzo, soxta imzo rad etilishi, noto‘g‘ri summa,
mavjud bo‘lmagan buyurtma, takroriy Complete (huquq ikki marta berilmasligi)
va bekor qilingan to‘lov.

**`phase0test.py`** — tezlik o‘lchovi va analitika: migratsiyalar (ikki
marta ishlaganda ham xatosiz, eski ma’lumot o‘zgarmaydi), manba (deep link —
faqat birinchisi saqlanadi), voronka hodisalari va test ichidagi 25/50/75 %
bosqichlar, to‘lov hodisasi bir marta, bloklash/qaytish, bitta tugma
bosishga bitta javob, `/stats` va `/perf`.

**`phase2test.py`** — o‘sish halqalari: do‘st mukofoti (faqat yangi odam,
bir marta, oylik chegara, o‘chirsa bo‘ladi) va bepul tahlilni ishlatish,
do‘st bilan solishtirish (faqat havolani bosganga, foizlarsiz), promo kodlar
(admin yaratadi; limit, muddat, chegirma bitta to‘lovga), sertifikat ostidagi
ulashish matni (Farzand testida bolaning natijasi yo‘q), bir martalik e’lon
(bloklaganlar o‘tkaziladi, ikki marta ketmaydi), eslatmalar (3 soat / 24 soat,
7 kunda 2 ta, 23:00–08:00 jim, «kerak emas») va `/stats`.

**`tools/speedbench.py`** — har bir handler foydalanuvchini qancha kutdirishi
(Telegram o‘rnida har so‘rovga 40 ms kechikishli soxta sessiya).

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
| `psytests/iq.py` | IQ topshiriqlari tartibi, taxminiy IQ hisobi, daraja (javoblar kaliti — serverdagi `IQ_ANSWERS` da) |
| `assets/iq/` | IQ rasmlari (A–D variantlari rasmning o‘zida) |
| `handlers/iq.py` | IQ oqimi: yosh, rasm, A–D tugmalari, taxminiy IQ bilan natija |
| `content_cms.py` | savollar CMS jadvali va migratsiyasi |
| `psytests/__init__.py` | reyestr, yosh guruhlari, yosh maslahatlari |
| `report.py` | natija matnini yig‘ish |
| `keyboards.py` | inline tugmalar |
| `database.py` | SQLite + eski bazadan avtomatik ko‘chirish |
| `migrations.py` | sxema o‘zgarishlari — raqamlangan, faqat qo‘shiladi, `schema_migrations` da qayd |
| `events.py` | analitika hodisalari (fonda, partiya bilan yoziladi) va deep link manbasi |
| `stats.py` | `/stats`: manbalar, voronka, tushum, bloklar (60 s kesh) |
| `perf.py` | tezlik o‘lchovi: har update uchun `perf` qatori, `/perf`, tugma javobi fonda |
| `handlers/admin_stats.py` | `/stats` va `/perf` ekranlari |
| `handlers/admin_growth.py` | admin «🚀 O‘sish»: do‘st mukofoti, eslatmalar, promo kodlar, bir martalik e’lon |
| `handlers/loops.py` | bepul tahlil, do‘st bilan solishtirish, promo kod, eslatmani o‘chirish tugmalari |
| `referral_rewards.py` | do‘st mukofoti qoidalari (yangi odam testni tugatsa — 1 ta bepul tahlil, oyiga chegara) |
| `credits.py` | bepul ochish huquqi («1 ta to‘liq tahlil — o‘zingiz tanlaysiz») |
| `compare.py` | do‘st bilan solishtirish (Big Five, IQ) — foizlarsiz |
| `promo.py` | promo kodlar: bepul tahlil yoki chegirma, limit, muddat |
| `reminders.py` | avtomatik eslatmalar va ularning chegaralari |
| `broadcast.py` | ko‘pchilikka yuborish: bloklaganlar o‘tkaziladi, natija bazaga va log’ga |
| `handlers/lifecycle.py` | botni bloklash/qaytish, zararsiz «message is not modified» xatosi |
| `handlers/middleware.py` | foydalanuvchi va tilni aniqlash |
| `handlers/user.py` | menyu, test oqimi, natija |
| `handlers/admin.py` | statistika, to‘lovlar va ommaviy xabar |
| `handlers/payment.py` | paywall, Click havolasi, huquq tekshiruvi |
| `payments/click.py` | Click protokoli: imzo, havola, invoice (Telegramsiz) |
| `payments/webapp.py` | Click so‘rovlarini qabul qiladigan HTTP server |

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

- 📊 **Statistika** (`/stats`) — bugun / 7 kun / 30 kun: yangi foydalanuvchilar
  **manba bo‘yicha**, har bir test voronkasi (ochdi → boshladi → tugatdi →
  to‘lov oynasi → to‘ladi) va test ichida qayerda to‘xtashadi (25/50/75 %),
  tushum, sertifikatlar, taklif qilinganlar, bloklaganlar ulushi
- ⚡️ **Tezlik** (`/perf`) — har bir buyruq/tugma uchun p50/p95/max (ms),
  bazada va Telegram'da o‘tgan vaqt
- 📣 **Xabar yuborish** — hammaga, faqat o‘zbekchaga yoki faqat ruschaga.
  Tasdiqlash so‘raladi, bloklaganlar avtomatik belgilanadi
- 🚀 **O‘sish** — do‘st mukofoti (yoqish/o‘chirish, oylik chegara), eslatmalar
  (yoqish/o‘chirish), 🎟 promo kodlar (yaratish, havolasi, o‘chirish) va
  📣 bir martalik yangilik e’loni (oldin ko‘rinishi va oluvchilar soni)
- 💳 **To‘lovlar** — tushum, oxirgi to‘lovlar, to‘liq tahlil narxlari (va
  to‘plam), to‘liq tahlilni vaqtincha bepul qilish, qo‘lda ochish, «Chekdan
  oldin ochish» (odatda o‘chiq), **Click to‘ldirishlarini tekshirish** (eski
  xato tufayli balansga tushmagan to‘ldirishlarni topib, bir marta tushiradi)

---

## Pul modeli: test bepul, to‘liq tahlil pullik

- Hamma test **bepul topshiriladi**. Natijadan keyin **qisqa natija va
  sertifikat bepul**; **to‘liq tahlil** — pullik (har bir test narxi admin
  panelda, «📦 5 ta test to‘plami» — alohida narx).
- Nima bepul, nima pullik — **test boshlanishidan oldin** aytiladi.
- Avval testni sotib olganlar o‘sha testning to‘liq tahlilini bepul ko‘radi
  (migratsiya 5: `report_access`, source = `legacy`).
- To‘lov ekrani: **avval Click** (aynan tahlil narxiga, balans emas),
  **keyin karta** (summa va karta raqami ko‘rsatiladi → odam faqat chek
  rasmini yuboradi → chek **adminlarga ID bo‘yicha** tasdiqlash/rad etish
  tugmalari bilan boradi), balans yetarli bo‘lsa — balansdan.
- To‘lovdan keyin to‘liq tahlil **shu chatda darhol** ochiladi.
- **IQ:** bepul natijada **hech qanday raqam yo‘q** — na taxminiy IQ, na to‘g‘ri
  javoblar soni (egasining qarori: past ball odamni xafa qiladi, raqam esa
  natijani oldindan aytib qo‘yadi). Bepul: eng kuchli fikrlash turi va
  raqamsiz sertifikat. To‘lovdan keyin to‘liq tahlil va — taxminiy IQ 100 va
  undan yuqori bo‘lsa — **«IQ 112» yozilgan sertifikat o‘zi keladi**
  («Ballni yashirish» tugmasi bilan). «📈 Natijalarim» da ham IQ raqami faqat
  to‘liq tahlil ochiq bo‘lsa ko‘rinadi.
- «⚡️ Chekdan oldin ochish» (admin → To‘lovlar, **odatda o‘chiq**): 5 000
  so‘mgacha chek rasmi kelishi bilan ochiladi; bir odamda bir vaqtda bitta;
  rad etilsa — yopiladi va u odamga bu imkoniyat boshqa berilmaydi.
- Test o‘rtasida javoblar bazaga yoziladi (`progress`): /start da «▶️ Testni
  davom ettirish (23/50)», bot qayta ishga tushsa ham eski savol tugmasi ishlaydi.

**To‘liq tahlil matnlari** — `content/reports.toml` (kodga tegmasdan
tahrirlanadi; hammasi DRAFT, egasi ko‘rib chiqishi kerak). `selftest.py`
ularni ham tekshiradi (apostroflar, kitobiy so‘zlar).

---

## O‘sish halqalari (2-bosqich)

- **Do‘st taklifi.** Har kimning havolasi `?start=ref_<id>`. Shu havola orqali
  botga **birinchi marta** kelgan odam birorta testni oxirigacha topshirsa,
  taklif qilganga **1 ta bepul to‘liq tahlil** (qaysi test — o‘zi tanlaydi).
  Har bir yangi odam uchun bir marta, oyiga ko‘pi bilan 10 ta (admin
  panelda o‘zgaradi). O‘zini taklif qilish va eski foydalanuvchilar
  hisoblanmaydi. Taklif qilganga bir marta xabar boradi.
- **Do‘st bilan solishtirish** (Big Five va IQ). Natija ostida «👥 Do‘stingiz
  bilan solishtiring» → `?start=cmp_<test>_<id>`. Do‘st testni bepul
  topshirgach, **faqat unga** qisqa solishtirish chiqadi: kimda qaysi
  xususiyat ko‘proq — **foiz va ballsiz**. To‘liq tahlil pullik bo‘lib qoladi.
- **Promo kodlar** (hamkorlar: o‘quv markazlar, maktablar, blogerlar). Bepul
  to‘liq tahlil (tanlangan testlar) yoki chegirma % (keyingi bitta to‘lovga),
  nechta odam, necha kun, izoh. Odam kodni havola (`?start=promo_KOD`) yoki
  `/promo KOD` bilan kiritadi. `/stats` da har bir kod alohida.
- **Ulashish matni** sertifikat ostida, odamning tilida va shaxsiy taklif
  havolasi bilan: «Men «Qonuniyat ovchisi» chiqdim. Siz-chi? 👉». Farzand
  testida faqat test nomi — bolaning natijasi hech qayerga chiqmaydi.
- **Bir martalik e’lon** (admin bosadi): bloklaganlarga yuborilmaydi, Telegram
  cheklovi hisobga olinadi, natija (yetdi / bloklagan / xato) yoziladi, ikki
  marta ketmaydi. Oddiy «📣 Xabar yuborish» ham shu yo‘l bilan ishlaydi.
- **Eslatmalar** (admin panelda o‘chiriladi): tashlab ketilgan test — ~3 soatdan
  keyin bitta; ochilmagan to‘liq tahlil — ~24 soatdan keyin bitta (bosimsiz).
  Bitta odamga 7 kunda 2 tadan ko‘p emas, 23:00–08:00 (Toshkent) jim, har bir
  xabarda «🔕 Eslatma kerak emas».

Bazadagi o‘zgarishlar — migratsiya 6 (faqat yangi jadvallar qo‘shiladi).

---

## Reklama havolalari (manba)

Har bir reklama uchun alohida havola bering — `/stats` qaysi biri odam
olib kelganini ko‘rsatadi:

```
https://t.me/kelajak_testi_bot?start=src_instagram
https://t.me/kelajak_testi_bot?start=src_youtube
https://t.me/kelajak_testi_bot?start=src_tgads_<kanal>
https://t.me/kelajak_testi_bot?start=ref_<user_id>      (do‘st taklifi)
https://t.me/kelajak_testi_bot?start=promo_<kod>        (hamkor kodi → manba promo_<kod>)
https://t.me/kelajak_testi_bot?start=cmp_bigfive_<id>   (do‘st bilan solishtirish → manba cmp)
```

Foydalanuvchining **birinchi** manbasi saqlanadi va keyin o‘zgarmaydi.
Havolasiz kelgan yangi odam — `direct`; manba yozilishidan oldin kelganlar —
`noma’lum`.

---

## To‘lov (Click)

Testlar **pullik**: test faqat to‘lov Click tomonidan tasdiqlangandan keyin
ochiladi. To‘lov `my.click.uz` havolasi orqali — karta bilan yoki Click Up
ilovasida.

Huquq **faqat bitta joyda** beriladi: Click ning `/click/complete` so‘rovi
kelganda. Botdagi «To‘ladim» tugmasi ham o‘zicha hech narsa ochmaydi — u
Click API dan holatni so‘raydi. Ya‘ni to‘lamay turib testga kirish yo‘li
yo‘q.

Bot endi **web-servis** (avval `worker` edi): Click bizga so‘rov yuborishi
uchun ochiq manzil kerak. Ochiladigan yo‘llar:

| Yo‘l | Kim so‘raydi |
|---|---|
| `POST /click/prepare` | Click — «buyurtma bormi, summa to‘g‘rimi?» |
| `POST /click/complete` | Click — «pul yechildi, xizmatni bering» |
| `GET /click/return` | to‘lovdan keyin odam tushadigan sahifa |
| `GET /health` | platformaning sog‘liq tekshiruvi |

Sozlash bo‘yicha to‘liq qo‘llanma — **[CLICK.md](CLICK.md)**: merchant
kabinetiga nima yozish, Click‘ga qanday xabar yuborish, statik IP masalasi.

---

## Deploy (Railway)

`Dockerfile`, `Procfile` va `railway.json` tayyor. Muhit o‘zgaruvchilarini
Railway panelida qo‘ying, `.env` faylini serverga yuklamang:

```
BOT_TOKEN, ADMIN_ID, BOT_USERNAME, DB_PATH
CLICK_SERVICE_ID, CLICK_MERCHANT_ID, CLICK_SECRET_KEY, CLICK_MERCHANT_USER_ID
PUBLIC_URL, PRICE_UZS, PRICE_ALL_UZS
```

`PUBLIC_URL` — Railway bergan ochiq domen (**Settings → Networking →
Generate Domain**), oxirida `/` bo‘lmasin. U bo‘sh bo‘lsa Click to‘lov
haqida xabar bera olmaydi va hech kimga test ochilmaydi — bot ishga
tushganda logda ogohlantirish chiqadi.

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
