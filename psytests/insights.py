"""Natija uchun qo'shimcha mazmun: har bir yo'nalish hayotda nimani anglatadi,
uni qanday mashq qilish mumkin, va natija rasmidagi (sertifikat) sarlavhalar.

Bu yerda faqat matn — hisob-kitob va chizish `report.py` va `result_image.py`
da. Hamma matn o'zbek va rus tilida, `selftest.py` ularni boshqa matnlar kabi
tekshiradi (apostroflar, kitobiy so'zlar, uzunlik).

Mashqlar ataylab testlardagi "past" izohlardagi maslahatdan boshqacha
yozilgan — hisobotda bitta maslahat ikki marta takrorlanmasin.
"""
from __future__ import annotations

from dataclasses import dataclass

from .base import L


@dataclass(frozen=True)
class Insight:
    """Hisobotdagi bitta yo'nalish uchun ikki jumla."""

    #: Bu ko'nikma kundalik hayotda nimani anglatadi — bitta jumla.
    everyday: dict[str, str]
    #: Uni o'stirish uchun bitta aniq mashq — bitta jumla.
    exercise: dict[str, str]


@dataclass(frozen=True)
class Archetype:
    """Natija rasmidagi sarlavha va unga mos bitta qator."""

    name: dict[str, str]
    line: dict[str, str]


# --- Hisobot: har bir yo'nalish -------------------------------------------

INSIGHTS: dict[str, dict[str, Insight]] = {
    "bigfive": {
        "E": Insight(
            L("Yangi odamlar bilan qanchalik oson tanishishingiz va davrada o‘zingizni qanday his qilishingizni ko‘rsatadi.",
              "Показывает, насколько легко вы знакомитесь и как чувствуете себя в компании."),
            L("Bu hafta bitta notanish odam bilan o‘zingiz birinchi bo‘lib gaplashing — sinfdosh, hamkasb yoki qo‘shni bilan.",
              "На этой неделе первым заговорите с одним незнакомым человеком — одноклассником, коллегой или соседом."),
        ),
        "A": Insight(
            L("Odamlar bilan qanchalik yaxshi til topishishingiz va boshqalarga qanchalik e’tiborli ekaningizni bildiradi.",
              "Говорит о том, как вы ладите с людьми и насколько внимательны к другим."),
            L("Har kuni bitta odamning gapini bo‘lmasdan oxirigacha tinglang, keyin eshitganingizni o‘z so‘zingiz bilan qaytaring.",
              "Каждый день выслушайте одного человека до конца, не перебивая, а потом перескажите услышанное своими словами."),
        ),
        "C": Insight(
            L("Rejaga amal qilish, va’dani bajarish va boshlagan ishni oxiriga yetkazish qobiliyatingiz.",
              "Умение следовать плану, держать слово и доводить начатое до конца."),
            L("Har kechqurun ertangi uchta eng muhim ishni yozib qo‘ying va ertasi kuni birinchisidan boshlang.",
              "Каждый вечер записывайте три главных дела на завтра и начинайте день с первого из них."),
        ),
        "S": Insight(
            L("Stress, xato yoki kutilmagan voqeadan keyin qanchalik tez o‘zingizga kelishingizni ko‘rsatadi.",
              "Показывает, как быстро вы приходите в себя после стресса, ошибки или неожиданности."),
            L("Asabiylashganingizda 4 soniya nafas oling, 4 soniya ushlab turing va 6 soniyada chiqaring — buni 5 marta takrorlang.",
              "Когда нервничаете, вдохните на 4 счёта, задержите дыхание на 4 и выдохните на 6 — повторите 5 раз."),
        ),
        "O": Insight(
            L("Yangi g‘oya, bilim va tajribaga qanchalik qiziqishingiz hamda tasavvuringiz kuchini bildiradi.",
              "Говорит о том, насколько вам интересны новые идеи, знания и опыт, и о силе воображения."),
            L("Haftada bir marta umuman bilmagan mavzungiz haqida 15 daqiqa o‘qing yoki video ko‘ring va bitta yangi fikrni yozib qo‘ying.",
              "Раз в неделю 15 минут читайте или смотрите видео о совсем незнакомой теме и запишите одну новую мысль."),
        ),
    },
    "future": {
        "maqsad": Insight(
            L("Uzoq muddatli maqsadga qiyinchilik bo‘lsa ham intilib borish qobiliyati.",
              "Способность идти к долгосрочной цели, даже когда трудно."),
            L("Bitta maqsadni haftalik kichik qadamlarga bo‘ling va har yakshanba bajarilganlarini belgilab boring.",
              "Разбейте одну цель на недельные шаги и каждое воскресенье отмечайте выполненное."),
        ),
        "intizom": Insight(
            L("Kerakli ishni kayfiyat bo‘lmasa ham o‘z vaqtida bajarish odati.",
              "Привычка делать нужное вовремя, даже без настроения."),
            L("Katta ishni bo‘laklarga bo‘ling: 25 daqiqa ishlang, 5 daqiqa dam oling va shuni to‘rt marta takrorlang.",
              "Делите большие дела на отрезки: 25 минут работы, 5 минут отдыха — и так четыре раза."),
        ),
        "tafakkur": Insight(
            L("Xatodan saboq olib, yangi narsani o‘rganishdan qo‘rqmaslik.",
              "Умение учиться на ошибках и не бояться нового."),
            L("Har kuni kechqurun «Bugun nimani o‘rgandim?» degan savolga bitta gap bilan yozma javob bering.",
              "Каждый вечер одной фразой письменно отвечайте на вопрос: «Чему я сегодня научился?»"),
        ),
        "nazorat": Insight(
            L("Hozirgi istakni katta maqsad uchun keyinga qoldira olish.",
              "Умение отложить сиюминутное желание ради большой цели."),
            L("Telefonga qo‘l cho‘zganingizda 2 daqiqa kuting — shu vaqt ichida istak ko‘pincha o‘tib ketadi.",
              "Когда тянетесь к телефону, подождите 2 минуты — за это время желание часто проходит."),
        ),
        "mustaqillik": Insight(
            L("Hayotingizni omad emas, o‘z qarorlaringiz o‘zgartirishiga ishonch.",
              "Уверенность в том, что жизнь меняют ваши решения, а не удача."),
            L("Har kuni o‘zingiz qilgan bitta kichik tanlovni va u nimaga olib kelganini yozib boring.",
              "Каждый день записывайте один свой маленький выбор и то, к чему он привёл."),
        ),
        "muloqot": Insight(
            L("Qiyin paytda tayanadigan yaqinlaringiz bor-yo‘qligi va yangi aloqa qura olishingiz.",
              "Есть ли близкие, на которых можно опереться, и умеете ли вы заводить новые связи."),
            L("Bu hafta uzoq vaqt gaplashmagan bitta tanishingizga o‘zingiz yozing yoki qo‘ng‘iroq qiling.",
              "На этой неделе сами напишите или позвоните знакомому, с которым давно не общались."),
        ),
        "bardosh": Insight(
            L("Muvaffaqiyatsizlikdan keyin tez tiklanish va bosim ostida ham aniq fikrlash.",
              "Быстро восстанавливаться после неудач и ясно мыслить под давлением."),
            L("Stressli vaziyatdan keyin 10 daqiqa yurib keling yoki ishonchli odamga gapirib bering — hissiyotni ichingizda saqlamang.",
              "После стрессовой ситуации 10 минут пройдитесь или расскажите о ней близкому человеку — не держите всё в себе."),
        ),
        "uyqu": Insight(
            L("Uyqu va harakat — diqqat, xotira va kayfiyatingizning asosi.",
              "Сон и движение — основа внимания, памяти и настроения."),
            L("Har kuni kamida 20 daqiqa tez yuring — bu uyquni ham, kayfiyatni ham yaxshilaydi.",
              "Каждый день минимум 20 минут быстро ходите пешком — это улучшает и сон, и настроение."),
        ),
        "ichki": Insight(
            L("Hayotingizda ma’no ko‘rish va boringizni qadrlay olish.",
              "Умение видеть смысл в жизни и ценить то, что у вас есть."),
            L("Haftada bir marta sizga yordam bergan odamga rahmat ayting va nima uchun minnatdor ekaningizni aniq ayting.",
              "Раз в неделю поблагодарите человека, который вам помог, и скажите, за что именно."),
        ),
    },
    "career": {
        "R": Insight(
            L("Qo‘l bilan ishlashni, asbob va texnika bilan natijani ko‘z bilan ko‘rishni yoqtirish.",
              "Любовь к работе руками, с инструментами и техникой, когда результат видно глазами."),
            L("Uydagi buzilgan bitta narsani video yo‘riqnoma bo‘yicha o‘zingiz tuzatib ko‘ring.",
              "Попробуйте сами починить одну сломанную вещь дома по видеоинструкции."),
        ),
        "I": Insight(
            L("Narsalarning sababini tushunish, tahlil qilish va murakkab masalani yechishga qiziqish.",
              "Интерес к причинам вещей, анализу и сложным задачам."),
            L("Har hafta bitta «nega?» degan savolni tanlang va javobini ishonchli manbalardan izlab toping.",
              "Каждую неделю выбирайте один вопрос «почему?» и ищите ответ в надёжных источниках."),
        ),
        "A": Insight(
            L("Yangi narsa yaratish, o‘zini ifodalash va tayyor qolipsiz ishlash istagi.",
              "Желание создавать новое, выражать себя и работать без шаблонов."),
            L("Bir hafta ichida kichik ijodiy ish yarating — rasm, qisqa video yoki hikoya — va uni bitta odamga ko‘rsating.",
              "За неделю создайте небольшую творческую работу — рисунок, короткое видео или рассказ — и покажите её кому-нибудь."),
        ),
        "S": Insight(
            L("Odamlarga yordam berish, tushuntirish va ularning o‘sishini ko‘rishdan quvvat olish.",
              "Энергия от помощи людям, объяснения и того, как они растут."),
            L("Bu hafta sinfdoshingiz yoki ukangizga bitta mavzuni tushuntirib bering va u tushunganini tekshiring.",
              "На этой неделе объясните одну тему однокласснику или младшему и проверьте, понял ли он."),
        ),
        "E": Insight(
            L("Boshqarish, odamlarni ishontirish va natija uchun javobgarlikni olishga qiziqish.",
              "Интерес к руководству, убеждению людей и ответственности за результат."),
            L("Kichik loyiha boshlang — masalan, sinf tadbiri yoki kichik savdo — va uni oxirigacha o‘zingiz boshqaring.",
              "Начните маленький проект — например, классное мероприятие или небольшую продажу — и доведите его до конца сами."),
        ),
        "C": Insight(
            L("Aniqlik, tartib va aniq qoidalar bo‘yicha ishlashni qadrlash.",
              "Ценность точности, порядка и работы по чётким правилам."),
            L("Bir oy davomida xarajatlaringizni jadvalga yozib boring va oy oxirida xulosa chiqaring.",
              "Месяц записывайте свои расходы в таблицу и в конце месяца подведите итог."),
        ),
    },
    "child": {
        "boshqaruv": Insight(
            L("Farzandingiz diqqatini jamlay olishi, xohlaganini kuta bilishi va jahlini boshqara olishi.",
              "Умение ребёнка сосредоточиться, подождать желаемого и справиться со злостью."),
            L("Birga «Qotib qol» o‘yinini o‘ynang: musiqa to‘xtaganda hamma qotib qoladi — bu o‘zini to‘xtatishni o‘rgatadi.",
              "Играйте вместе в «Замри»: когда музыка останавливается, все замирают — это учит останавливать себя."),
        ),
        "qiziqish": Insight(
            L("Yangi narsaga qiziqishi, savol berishi va o‘rganishni o‘zi xohlashi.",
              "Интерес к новому, вопросы и желание учиться самому."),
            L("Haftada bir marta birga kichik tajriba qiling — masalan, suvda nima cho‘kadi, nima suzadi — va natijani muhokama qiling.",
              "Раз в неделю проводите вместе маленький опыт — например, что тонет, а что плавает — и обсуждайте результат."),
        ),
        "tafakkur": Insight(
            L("Qiyin vazifadan qochmasligi va xatoni o‘rganish imkoniyati deb bilishi.",
              "Не избегает трудных задач и видит в ошибке возможность научиться."),
            L("Kechki ovqatda har kim bugungi bitta xatosi va undan nimani o‘rganganini aytib bersin — o‘zingizdan boshlang.",
              "За ужином пусть каждый расскажет об одной своей ошибке за день и чему она научила — начните с себя."),
        ),
        "ijtimoiy": Insight(
            L("Tengdoshlari bilan do‘stlashishi, boshqaning holatini tushunishi va nizoni so‘z bilan hal qilishi.",
              "Умение дружить со сверстниками, понимать других и решать споры словами."),
            L("Farzandingizning bitta do‘stini uyga taklif qiling va ularga birga o‘ynashlari uchun vaqt ajrating.",
              "Пригласите домой одного друга ребёнка и дайте им время поиграть вместе."),
        ),
        "mehnat": Insight(
            L("Uy yumushi va vazifani eslatmasdan, mas’uliyat bilan bajarishi.",
              "Выполнение домашних дел и заданий без напоминаний, с ответственностью."),
            L("Yumushlar jadvalini birga tuzing va bajarilganini farzandingiz o‘zi belgilab borsin.",
              "Составьте вместе таблицу обязанностей, и пусть ребёнок сам отмечает выполненное."),
        ),
        "oila": Insight(
            L("Uyda farzandingiz o‘zini xavfsiz, tinglangan va qadrlangan his qilishi.",
              "Дома ребёнок чувствует себя в безопасности, услышанным и ценным."),
            L("Har kuni uxlashdan oldin 5 daqiqa «Bugun nima yoqdi, nima yoqmadi?» deb suhbatlashing.",
              "Каждый вечер перед сном 5 минут поговорите: «Что сегодня понравилось, а что нет?»"),
        ),
        "sogliq": Insight(
            L("Yetarli uyqu, harakat va ekran vaqtining muvozanati — diqqat va kayfiyat asosi.",
              "Баланс сна, движения и экранного времени — основа внимания и настроения."),
            L("Har kuni birga kamida 30 daqiqa ochiq havoda harakat qiling — yurish, velosiped yoki to‘p o‘yini.",
              "Каждый день хотя бы 30 минут двигайтесь вместе на свежем воздухе — прогулка, велосипед или игра в мяч."),
        ),
        "hissiyot": Insight(
            L("His-tuyg‘ularini tushunishi, ularni aytib bera olishi va yangilikka moslasha olishi.",
              "Умение понимать свои чувства, говорить о них и привыкать к новому."),
            L("Birga «kayfiyat kartochkalari» chizing (quvnoq, xafa, jahldor) va har kuni farzandingiz bittasini ko‘rsatsin.",
              "Нарисуйте вместе «карточки настроения» (радость, грусть, злость), и пусть ребёнок каждый день показывает одну."),
        ),
    },
}


# --- Natija rasmi: sarlavhalar -------------------------------------------

ARCHETYPES: dict[str, dict[str, Archetype]] = {
    "bigfive": {
        "E": Archetype(L("Davra yulduzi", "Звезда компании"),
                       L("Odamlar orasida quvvat olasiz va boshqalarni ham ruhlantirasiz.",
                         "Вы заряжаетесь среди людей и заряжаете других.")),
        "A": Archetype(L("Mehribon qalb", "Доброе сердце"),
                       L("Odamlar sizga ishonadi va yoningizda o‘zini erkin his qiladi.",
                         "Люди вам доверяют, и рядом с вами им спокойно.")),
        "C": Archetype(L("Ishonchli strateg", "Надёжный стратег"),
                       L("Aytganingizni qilasiz va boshlagan ishni oxiriga yetkazasiz.",
                         "Вы держите слово и доводите начатое до конца.")),
        "S": Archetype(L("Xotirjam kuch", "Спокойная сила"),
                       L("Bosim ostida ham sovuqqon qolasiz va tez tiklanasiz.",
                         "Под давлением вы сохраняете хладнокровие и быстро восстанавливаетесь.")),
        "O": Archetype(L("Ijodkor aql", "Творческий ум"),
                       L("Yangi g‘oyalar sizni o‘ziga tortadi, tasavvuringiz esa chegarasiz.",
                         "Новые идеи вас притягивают, а воображение не знает границ.")),
    },
    "future": {
        "maqsad": Archetype(L("Maqsad sari intiluvchi", "Целеустремлённый"),
                            L("Katta maqsadga yillab intila olasiz — bu kam odamda bor.",
                              "Вы годами идёте к большой цели — это редкое качество.")),
        "intizom": Archetype(L("Intizom ustasi", "Мастер дисциплины"),
                             L("Reja tuzasiz va unga amal qilasiz — natija shundan boshlanadi.",
                               "Вы составляете план и следуете ему — с этого начинается результат.")),
        "tafakkur": Archetype(L("Doim o‘sib boruvchi", "Вечный ученик"),
                              L("Har bir xatodan saboq olib, yanada kuchliroq bo‘lasiz.",
                                "Из каждой ошибки вы выносите урок и становитесь сильнее.")),
        "nazorat": Archetype(L("O‘zini boshqara oladigan", "Хозяин своих желаний"),
                             L("Bugungi istakni ertangi katta natijaga almashtira olasiz.",
                               "Вы умеете менять сиюминутное желание на большой результат завтра.")),
        "mustaqillik": Archetype(L("O‘z hayotining muallifi", "Автор своей жизни"),
                                 L("Natija uchun javobgarlikni o‘zingiz olasiz — bu eng ishonchli poydevor.",
                                   "Вы берёте ответственность за результат на себя — это самая надёжная основа.")),
        "muloqot": Archetype(L("Aloqalar ustasi", "Мастер общения"),
                             L("Atrofingizdagi odamlar — sizning eng katta boyligingiz.",
                               "Люди вокруг вас — ваше главное богатство.")),
        "bardosh": Archetype(L("Sinmas ruh", "Несгибаемый дух"),
                             L("Qiyinchilikdan keyin tez tiklanib, yana oldinga intilasiz.",
                               "После трудностей вы быстро встаёте и снова идёте вперёд.")),
        "uyqu": Archetype(L("Energiya manbai", "Источник энергии"),
                          L("Uyqu va harakatingiz joyida — diqqat va kayfiyatingizning siri shunda.",
                            "Сон и движение в порядке — в этом секрет вашего внимания и настроения.")),
        "ichki": Archetype(L("Ichki boylik egasi", "Внутренне богатый человек"),
                           L("Hayotingizda ma’no bor va boringizni qadrlay olasiz.",
                             "В вашей жизни есть смысл, и вы цените то, что имеете.")),
    },
    "career": {
        "R": Archetype(L("Amaliy usta", "Мастер-практик"),
                       L("Sizga mos: muhandis, mexanik, elektrik, quruvchi.",
                         "Вам подходит: инженер, механик, электрик, строитель.")),
        "I": Archetype(L("Tadqiqotchi aql", "Ум исследователя"),
                       L("Sizga mos: dasturchi, ma’lumot tahlilchisi, shifokor, olim.",
                         "Вам подходит: программист, аналитик данных, врач, учёный.")),
        "A": Archetype(L("Ijodkor ruh", "Творческая натура"),
                       L("Sizga mos: dizayner, kontent yaratuvchi, videograf.",
                         "Вам подходит: дизайнер, создатель контента, видеограф.")),
        "S": Archetype(L("Odamlar ustozi", "Наставник для людей"),
                       L("Sizga mos: o‘qituvchi, psixolog, shifokor, murabbiy.",
                         "Вам подходит: учитель, психолог, врач, тренер.")),
        "E": Archetype(L("Tug‘ma yetakchi", "Прирождённый лидер"),
                       L("Sizga mos: tadbirkor, sotuv menejeri, loyiha rahbari.",
                         "Вам подходит: предприниматель, менеджер по продажам, руководитель проектов.")),
        "C": Archetype(L("Tartib ustasi", "Мастер порядка"),
                       L("Sizga mos: buxgalter, moliyachi, auditor, bank xodimi.",
                         "Вам подходит: бухгалтер, финансист, аудитор, банковский специалист.")),
    },
    "child": {
        "boshqaruv": Archetype(L("O‘zini tuta oladigan", "Умеет владеть собой"),
                               L("Diqqatini jamlay oladi va xohlaganini kuta biladi.",
                                 "Умеет сосредоточиться и дождаться желаемого.")),
        "qiziqish": Archetype(L("Kichik tadqiqotchi", "Маленький исследователь"),
                              L("Dunyoni savollar orqali o‘rganadi — bu bilimga eng yaxshi yo‘l.",
                                "Познаёт мир через вопросы — лучший путь к знаниям.")),
        "tafakkur": Archetype(L("Qiyinchilikdan qo‘rqmaydigan", "Не боится трудностей"),
                              L("Xatodan uyalmaydi va qayta urinib ko‘radi.",
                                "Не стыдится ошибок и пробует снова.")),
        "ijtimoiy": Archetype(L("Do‘stlar markazi", "Душа компании"),
                              L("Tengdoshlari bilan til topishadi va boshqalarga hamdard bo‘la oladi.",
                                "Ладит со сверстниками и умеет сочувствовать.")),
        "mehnat": Archetype(L("Kichik yordamchi", "Маленький помощник"),
                            L("Mas’uliyatni his qiladi va yordam berishni yoqtiradi.",
                              "Чувствует ответственность и любит помогать.")),
        "oila": Archetype(L("Mehr bilan o‘sayotgan", "Растёт в любви"),
                          L("Uyda o‘zini xavfsiz va tinglangan his qiladi — bu eng kuchli tayanch.",
                            "Дома чувствует себя в безопасности и услышанным — это самая сильная опора.")),
        "sogliq": Archetype(L("Energiyaga to‘la", "Полон энергии"),
                            L("Uyqu va harakati joyida — diqqat va kayfiyat shundan boshlanadi.",
                              "Сон и движение в порядке — отсюда внимание и настроение.")),
        "hissiyot": Archetype(L("Tuyg‘ularini tushunadigan", "Понимает свои чувства"),
                              L("His-tuyg‘ularini ayta oladi va yangilikdan qo‘rqmaydi.",
                                "Умеет говорить о чувствах и не боится нового.")),
    },
    # IQ: taxminiy IQ 100 dan past bo'lsa, raqam o'rniga eng kuchli topshiriq
    # turi ko'rsatiladi (kalitlar — psytests.iq.KINDS).
    "iq": {
        "change": Archetype(L("Qonuniyat ovchisi", "Охотник за закономерностями"),
                            L("O‘zgarishlar ortidagi qoidani tez sezasiz.",
                              "Вы быстро замечаете правило за изменениями.")),
        "combine": Archetype(L("Shakllar ustasi", "Мастер фигур"),
                             L("Shakllarni xayolan birlashtirib, yangi butunlikni ko‘rasiz.",
                               "Вы мысленно соединяете фигуры и видите целое.")),
        "spatial": Archetype(L("Fazoviy tafakkur egasi", "Пространственный ум"),
                             L("Burilish va aksni xayolingizda aniq tasavvur qilasiz.",
                               "Вы точно представляете повороты и отражения.")),
        "rows": Archetype(L("Mantiq quruvchisi", "Строитель логики"),
                          L("Qatorlardagi tartibni ko‘rib, yetishmayotganini topasiz.",
                            "Вы видите порядок в рядах и находите недостающее.")),
    },
}

#: Taxminiy IQ 100 va undan yuqori bo'lganda rasmdagi daraja va qator.
#: (min_iq, daraja, qator) — kamayish tartibida.
IQ_LEVELS: list[tuple[int, dict[str, str], dict[str, str]]] = [
    (130, L("Juda yuqori daraja", "Очень высокий уровень"),
     L("Bunday natija taxminan har 50\u00a0kishidan birida uchraydi.",
       "Такой результат — примерно у 1\u00a0из 50\u00a0человек.")),
    (120, L("Yuqori daraja", "Высокий уровень"),
     L("Bunday natija taxminan har 10\u00a0kishidan birida uchraydi.",
       "Такой результат — примерно у каждого десятого.")),
    (110, L("O‘rtachadan yuqori", "Выше среднего"),
     L("Qonuniyatlarni ko‘pchilikdan yaxshiroq ko‘rasiz.",
       "Вы видите закономерности лучше большинства.")),
    (100, L("Mustahkam mantiq", "Уверенная логика"),
     L("Mantiqiy fikrlashingiz mustahkam poydevorga ega.",
       "У вашего логического мышления прочный фундамент.")),
]

#: Hamma yo'nalish 0 bo'lgan kamdan-kam holat uchun: kuchli tomon deb
#: aytishga asos yo'q, shuning uchun halol, lekin ruhlantiruvchi sarlavha.
FALLBACK = Archetype(
    L("Yo‘l boshida", "В начале пути"),
    L("Birinchi qadam qo‘yildi — endi qayerdan o‘sishni bilasiz.",
      "Первый шаг сделан — теперь вы знаете, куда расти."),
)

#: Hisobot oxirida taklif qilinadigan keyingi test.
NEXT_TEST: dict[str, str] = {
    "bigfive": "career",
    "career": "future",
    "future": "iq",
    "child": "future",
    "iq": "career",
}


def all_texts():
    """(yo'l, ikki tilli matn) — selftest shu orqali hamma matnni tekshiradi."""
    for test, items in INSIGHTS.items():
        for key, ins in items.items():
            yield f"insights.{test}.{key}.everyday", ins.everyday
            yield f"insights.{test}.{key}.exercise", ins.exercise
    for test, items in ARCHETYPES.items():
        for key, arch in items.items():
            yield f"archetype.{test}.{key}.name", arch.name
            yield f"archetype.{test}.{key}.line", arch.line
    for min_iq, name, line in IQ_LEVELS:
        yield f"iq_level.{min_iq}.name", name
        yield f"iq_level.{min_iq}.line", line
    yield "fallback.name", FALLBACK.name
    yield "fallback.line", FALLBACK.line
