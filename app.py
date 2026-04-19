#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  НУМЕРОЛОГИЧЕСКИЙ БОТ v4.0 — ВИРУСНАЯ ВЕРСИЯ                   ║
║  • Помнит дату/имя — никогда не переспрашивает                  ║
║  • Умный парсинг — принимает ЛЮБОЙ формат даты                  ║
║  • 15+ разделов · Ежедневный совет · Геймификация               ║
║  • Интрига после каждого ответа · Встроенный вирус              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import telebot, json, os, re, random
from datetime import datetime, date, timedelta
from telebot import types
from io import BytesIO

# ─── REPORTLAB ────────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ─── КОНФИГ ───────────────────────────────────────────────────────────────────
import os
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PROVIDER_TOKEN      = ""
PRICE_FULL_REPORT   = 50
PRICE_COMPAT_REPORT = 150
PRICE_NAME_REPORT   = 75
PRICE_YEAR_REPORT   = 50
PRICE_FORECAST      = 99   # Прогноз на 3 месяца
PRICE_KARMA         = 75   # Кармический разбор

DISCLAIMER = "\n\n_⚠️ В развлекательных целях._"

# ─── ДАННЫЕ ───────────────────────────────────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(__file__), "numerology_data.json")
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ numerology_data.json не найден!")
        return {"destiny_numbers":{}, "compatibility":{}, "sales_messages":[]}

DATA = load_data()
bot  = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="Markdown")

# Хранилище: uid → {birth_date, name, destiny_number, ...}
user_profiles: dict[int, dict] = {}
user_states:   dict[int, dict] = {}

# ─── УМНЫЙ ПАРСИНГ ДАТЫ ───────────────────────────────────────────────────────

def smart_parse_date(text: str) -> date | None:
    """
    Принимает ЛЮБОЙ разумный формат:
    15.03.1990 · 15/03/1990 · 15-03-1990 · 15031990 · 1990-03-15
    15 03 1990 · 15,03,1990 · 15 марта 1990 · март 15 1990
    """
    text = text.strip()

    MONTHS_RU = {
        "январ": 1, "феврал": 2, "март": 3, "апрел": 4,
        "май": 5, "мая": 5, "июн": 6, "июл": 7, "август": 8,
        "сентябр": 9, "октябр": 10, "ноябр": 11, "декабр": 12,
    }

    # Текстовый месяц: "15 марта 1990" или "15 март 1990"
    text_lower = text.lower()
    for ru, mon in MONTHS_RU.items():
        if ru in text_lower:
            nums = re.findall(r"\d+", text)
            if len(nums) >= 2:
                parts = [int(n) for n in nums]
                # Определяем день и год
                year = next((p for p in parts if p > 1900), None)
                day  = next((p for p in parts if 1 <= p <= 31 and p != year), None)
                if day and year:
                    try: return date(year, mon, day)
                    except: pass

    # Убираем все нецифровые разделители → список чисел
    nums = re.findall(r"\d+", text)
    if not nums:
        return None

    # Формат ISO: 1990-03-15
    iso = re.match(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", text)
    if iso:
        try: return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except: pass

    if len(nums) == 3:
        d, m, y = int(nums[0]), int(nums[1]), int(nums[2])
        # Если первое число похоже на год — это ISO формат
        if d > 1900:
            d, m, y = y, m, d
        try: return date(y, m, d)
        except: pass

    # Слипшиеся цифры: 15031990 или 1990315
    raw = "".join(nums)
    if len(raw) == 8:
        for fmt in [
            (raw[:2], raw[2:4], raw[4:]),   # DDMMYYYY
            (raw[6:], raw[4:6], raw[:4]),   # YYYYMMDD → DDMMYYYY
        ]:
            try:
                return date(int(fmt[2]), int(fmt[1]), int(fmt[0]))
            except:
                pass

    return None


def smart_parse_name(text: str) -> str | None:
    """Принимает имя в любом регистре, убирает лишнее."""
    text = text.strip()
    # Убираем цифры и спецсимволы
    cleaned = re.sub(r"[^а-яёА-ЯЁa-zA-Z\s\-]", "", text).strip()
    if len(cleaned) < 2:
        return None
    return cleaned.title()

# ─── НУМЕРОЛОГИЯ ──────────────────────────────────────────────────────────────

def reduce_to_single(n: int) -> int:
    if n in (11, 22, 33): return n
    if n < 10: return n
    return reduce_to_single(sum(int(d) for d in str(n)))

def calc_destiny(d: date) -> int:
    return reduce_to_single(
        reduce_to_single(d.day) + reduce_to_single(d.month) + reduce_to_single(d.year)
    )

def calc_personal_year(d: date, year: int = None) -> int:
    y = year or datetime.now().year
    return reduce_to_single(reduce_to_single(d.day) + reduce_to_single(d.month) + reduce_to_single(y))

def calc_personal_month(d: date) -> int:
    py = calc_personal_year(d)
    return reduce_to_single(py + datetime.now().month)

def calc_personal_day(d: date) -> int:
    pm = calc_personal_month(d)
    return reduce_to_single(pm + datetime.now().day)

def calc_name_number(name: str) -> int:
    table = {
        'а':1,'б':2,'в':6,'г':3,'д':4,'е':5,'ё':5,'ж':2,'з':7,'и':1,
        'й':1,'к':2,'л':3,'м':4,'н':5,'о':7,'п':8,'р':9,'с':1,'т':2,
        'у':6,'ф':8,'х':5,'ц':4,'ч':9,'ш':2,'щ':2,'ъ':1,'ы':1,'ь':2,
        'э':5,'ю':6,'я':1,
        'a':1,'b':2,'c':3,'d':4,'e':5,'f':8,'g':3,'h':5,'i':1,'j':1,
        'k':2,'l':3,'m':4,'n':5,'o':7,'p':8,'q':1,'r':9,'s':1,'t':2,
        'u':6,'v':6,'w':6,'x':5,'y':1,'z':7,
    }
    total = sum(table.get(c.lower(), 0) for c in name if c.isalpha())
    return reduce_to_single(total) if total else 0

def calc_karma_number(d: date) -> int:
    """Кармическое число — из дня рождения."""
    return reduce_to_single(d.day)

def calc_soul_number(name: str) -> int:
    """Число души — только гласные."""
    vowels = set("аеёиоуыэюяaeiouy")
    table = {
        'а':1,'е':5,'ё':5,'и':1,'о':7,'у':6,'ы':1,'э':5,'ю':6,'я':1,
        'a':1,'e':5,'i':1,'o':7,'u':6,'y':1,
    }
    total = sum(table.get(c.lower(), 0) for c in name if c.lower() in vowels)
    return reduce_to_single(total) if total else 0

def calc_personality_number(name: str) -> int:
    """Число личности — только согласные."""
    vowels = set("аеёиоуыэюяaeiouy")
    table = {
        'б':2,'в':6,'г':3,'д':4,'ж':2,'з':7,'й':1,'к':2,'л':3,'м':4,
        'н':5,'п':8,'р':9,'с':1,'т':2,'ф':8,'х':5,'ц':4,'ч':9,'ш':2,
        'щ':2,'ъ':1,'ь':2,
        'b':2,'c':3,'d':4,'f':8,'g':3,'h':5,'j':1,'k':2,'l':3,'m':4,
        'n':5,'p':8,'q':1,'r':9,'s':1,'t':2,'v':6,'w':6,'x':5,'z':7,
    }
    total = sum(table.get(c.lower(), 0) for c in name
                if c.isalpha() and c.lower() not in vowels)
    return reduce_to_single(total) if total else 0

# ─── ЕЖЕДНЕВНЫЕ СОВЕТЫ (меняются каждый день) ────────────────────────────────

DAILY_AFFIRMATIONS = {
    1: ["Сегодня я иду первым — и это правильно.",
        "Моя уверенность открывает любые двери.",
        "Я лидирую не потому что должен — а потому что могу."],
    2: ["Сегодня я слушаю сердце, а не голову.",
        "Моя чуткость — это суперсила, а не слабость.",
        "В мире есть место для моей нежности."],
    3: ["Сегодня я говорю, пою и создаю.",
        "Мой голос — это мой подарок миру.",
        "Радость — это мой выбор прямо сейчас."],
    4: ["Сегодня я строю. Каждый шаг важен.",
        "Мой труд — это молитва в действии.",
        "Надёжность — моя коронная суперсила."],
    5: ["Сегодня я открыт переменам.",
        "Неизвестность — это приглашение к приключению.",
        "Свобода начинается внутри меня."],
    6: ["Сегодня я отдаю — и это возвращается.",
        "Моя любовь исцеляет всё вокруг.",
        "Забота о себе — это не эгоизм."],
    7: ["Сегодня я ищу глубину.",
        "За поверхностью всегда есть истина.",
        "Моя интуиция знает путь."],
    8: ["Сегодня деньги текут ко мне легко.",
        "Я заслуживаю успеха и изобилия.",
        "Моя сила создаёт реальность."],
    9: ["Сегодня я отпускаю то, что больше не служит.",
        "Моя мудрость — дар для тех, кто рядом.",
        "Я завершаю с благодарностью."],
    11: ["Сегодня я слушаю тишину между словами.",
        "Мой свет виден даже тогда, когда я молчу.",
        "Интуиция — мой компас."],
    22: ["Сегодня я строю нечто большее, чем себя.",
        "Мои планы меняют реальность.",
        "Я архитектор собственной судьбы."],
    33: ["Сегодня моя любовь исцеляет мир.",
        "Я несу свет туда, где темно.",
        "Служить — значит жить полностью."],
}

DAILY_WARNINGS = {
    1: "⚠️ Сегодня избегайте конфликтов из-за желания быть правым.",
    2: "⚠️ Не давайте обещаний, которые сложно выполнить.",
    3: "⚠️ Следите за словами — сегодня они острее обычного.",
    4: "⚠️ Не берите лишних обязательств — вы и так несёте достаточно.",
    5: "⚠️ Импульсивные решения сегодня могут обойтись дорого.",
    6: "⚠️ Не жертвуйте собой ради тех, кто не ценит это.",
    7: "⚠️ Избегайте паранойи — не все думают о плохом.",
    8: "⚠️ Деньги сегодня могут уйти так же быстро, как придут.",
    9: "⚠️ Не пытайтесь спасти всех — начните с себя.",
    11: "⚠️ Ваша чувствительность сегодня зашкаливает — меньше соцсетей.",
    22: "⚠️ Перфекционизм сегодня — ваш главный враг.",
    33: "⚠️ Берегите себя от чужой боли — вы не обязаны нести всё.",
}

KARMA_LESSONS = {
    1: "Ваш кармический урок — научиться принимать помощь. В прошлой жизни вы всё делали в одиночку — и это истощило душу.",
    2: "Ваш урок — говорить правду, даже когда это неудобно. Прошлые жизни научили вас молчать.",
    3: "Урок — доводить начатое до конца. Когда-то вы разбрасывали таланты, не реализуя ни один.",
    4: "Урок — позволить себе отдыхать без чувства вины. Вы работали слишком много жизней подряд.",
    5: "Урок — научиться оставаться. Когда-то вы убегали от всего, что требовало глубины.",
    6: "Урок — любить себя так же, как других. В прошлых жизнях вы отдавали, не получая ничего взамен.",
    7: "Урок — доверять людям. Когда-то предательство закрыло ваше сердце навсегда.",
    8: "Урок — понять, что деньги — инструмент, а не цель. Когда-то власть разрушила всё.",
    9: "Урок — отпускать без боли. Привязанность в прошлых жизнях стоила вам свободы.",
    10: "Урок — нести свет, не сгорая. Когда-то ваш дар стал вашим проклятием.",
    11: "Урок — заземляться. Ваша душа слишком долго жила в мире идей.",
    22: "Урок — строить для других, а не только для себя.",
    33: "Урок — принимать любовь, не только отдавать её.",
}

SECRET_TALENTS = {
    1: "🎯 Скрытый талант: вы можете стать символом целого поколения. В вас есть семена лидера, которого запомнят в истории.",
    2: "🔮 Скрытый талант: экстрасенсорная эмпатия. Вы чувствуете ложь и боль раньше, чем человек произносит слово.",
    3: "🎭 Скрытый талант: вы можете зажечь толпу одной фразой. Ваш голос — инструмент исцеления.",
    4: "🏛 Скрытый талант: вы можете построить систему, которая будет работать без вас столетиями.",
    5: "🌍 Скрытый талант: вы умеете читать людей с первого взгляда — как книгу без обложки.",
    6: "💊 Скрытый талант: исцеление прикосновением и словом. Рядом с вами люди выздоравливают.",
    7: "🔭 Скрытый талант: вы видите паттерны там, где другие видят хаос. Это дар учёного и мистика.",
    8: "💎 Скрытый талант: вы можете превратить любую идею в деньги — если захотите.",
    9: "🌊 Скрытый талант: вы меняете людей навсегда — одним разговором, одним взглядом.",
    11: "⚡ Скрытый талант: вы получаете информацию напрямую — минуя логику. Это называется ченнелинг.",
    22: "🌐 Скрытый талант: вы рождены изменить систему — образование, политику, науку.",
    33: "🕊 Скрытый талант: ваше присутствие само по себе исцеляет — даже без слов.",
}

PAST_LIFE_HINTS = {
    1: "В прошлой жизни вы были *правителем или полководцем*. Отсюда — врождённое ощущение, что вы знаете лучше других.",
    2: "В прошлой жизни вы были *целителем или монахом*. Отсюда — потребность в тишине и глубокая эмпатия.",
    3: "В прошлой жизни вы были *придворным поэтом или шутом короля*. Слова всегда были вашей силой.",
    4: "В прошлой жизни вы были *архитектором или каменщиком*. Руки помнят, как создавать вечное.",
    5: "В прошлой жизни вы были *торговцем или путешественником*. Дорога — это ваш настоящий дом.",
    6: "В прошлой жизни вы были *матерью большого семейства или жрицей*. Забота — это ваша природа.",
    7: "В прошлой жизни вы были *алхимиком или философом*. Истина всегда была важнее комфорта.",
    8: "В прошлой жизни вы были *банкиром или феодалом*. Власть над ресурсами — знакомое чувство.",
    9: "В прошлой жизни вы были *странствующим мудрецом*. Вас помнят те, кого вы уже не помните.",
    11: "В прошлой жизни вы были *оракулом или пифией*. Ваши пророчества меняли судьбы царств.",
    22: "В прошлой жизни вы были *строителем пирамид или храмов*. Масштаб — ваше естественное состояние.",
    33: "В прошлой жизни вы были *святым или шаманом*. Ваши молитвы исцеляли деревни.",
}

PERSONAL_YEAR_INFO = {
    1: ("🌱 Год посева", "Начало нового 9-летнего цикла. Всё, что посеете сейчас — будет расти 9 лет.", "Запускайте проекты, переезжайте, меняйте работу.", "Промедление и нерешительность."),
    2: ("🤝 Год партнёрств", "Год союзов и терпения. Лучше действовать вместе.", "Ищите союзников, укрепляйте отношения.", "Не торопите события."),
    3: ("🎨 Год творчества", "Творчество, общение, радость.", "Творите, путешествуйте, выражайте себя.", "Расточительность и поверхностность."),
    4: ("🏗 Год труда", "Время строить фундамент.", "Работайте системно, планируйте, экономьте.", "Не ждите быстрых результатов."),
    5: ("🌪 Год перемен", "Динамика, свобода, неожиданные повороты.", "Гибкость, новое, путешествия.", "Безрассудные риски."),
    6: ("🏠 Год семьи", "Дом, близкие, ответственность.", "Семья, дом, помощь другим.", "Не несите чужих проблем."),
    7: ("🔍 Год поиска", "Духовный поиск, самоанализ, учёба.", "Читайте, медитируйте, изучайте себя.", "Изоляция и депрессия."),
    8: ("💰 Год достижений", "Материальный успех, власть, признание.", "Просите повышения, запускайте бизнес.", "Не переусердствуйте."),
    9: ("🌅 Год завершений", "Закрытие старых глав.", "Прощайте, отпускайте, завершайте.", "Не цепляйтесь за прошлое."),
    11: ("⚡ Мастер-год интуиции", "Особый год духовных откровений.", "Доверяйте интуиции.", "Берегите нервы."),
    22: ("🏛 Мастер-год строителя", "Год реализации грандиозных планов.", "Мыслите глобально.", "Не распыляйтесь."),
    33: ("💝 Мастер-год учителя", "Год служения и любви.", "Помогайте, наставляйте.", "Не забывайте о себе."),
}

CHAKRA_BY_NUMBER = {
    1: ("🔴 Муладхара", "Корневая чакра — сила, выживание, земля.", "Красный гранат, гематит"),
    2: ("🟠 Свадхистхана", "Сакральная чакра — чувства, творчество.", "Оранжевый авантюрин, сердолик"),
    3: ("🟡 Манипура", "Солнечное сплетение — воля, уверенность.", "Цитрин, тигровый глаз"),
    4: ("🟢 Анахата", "Сердечная чакра — любовь, гармония.", "Розовый кварц, авантюрин"),
    5: ("🔵 Вишудха", "Горловая чакра — коммуникация, правда.", "Голубой топаз, аквамарин"),
    6: ("💜 Аджна", "Третий глаз — интуиция, мудрость.", "Аметист, лазурит"),
    7: ("🔮 Сахасрара", "Коронная чакра — просветление.", "Горный хрусталь, аметист"),
    8: ("🔴🟡 Двойная сила", "Муладхара + Манипура — земная мощь.", "Чёрный турмалин, пирит"),
    9: ("🌈 Все чакры", "Число завершения объединяет все центры.", "Радужный лунный камень"),
    11: ("⚡ Аджна×2", "Сверхактивный третий глаз.", "Лабрадорит, белый опал"),
    22: ("🔴🔮 Земля+небо", "Муладхара + Сахасрара — проводник.", "Обсидиан + горный хрусталь"),
    33: ("💝 Анахата×∞", "Сверхоткрытое сердце.", "Розовый турмалин"),
}

PLANET_BY_NUMBER = {
    1: ("☀️ Солнце", "Царь планет даёт харизму и жизненную силу.", "Золото, янтарь, хризолит"),
    2: ("🌙 Луна", "Наделяет интуицией и связью с подсознанием.", "Серебро, жемчуг, лунный камень"),
    3: ("♃ Юпитер", "Планета удачи и расширения.", "Топаз, сапфир"),
    4: ("♄ Сатурн", "Планета дисциплины и кармы.", "Оникс, обсидиан"),
    5: ("☿ Меркурий", "Планета коммуникации и скорости.", "Агат, бирюза"),
    6: ("♀ Венера", "Планета любви и красоты.", "Малахит, розовый кварц"),
    7: ("♆ Нептун", "Планета тайн и мистики.", "Аквамарин, аметист"),
    8: ("♄+♃ Дуэт", "Дисциплина + удача = успех.", "Сапфир, гранат"),
    9: ("♂ Марс", "Планета воли и действия.", "Рубин, красный коралл"),
    11: ("☿+🌙 Канал", "Молниеносная интуиция.", "Опал, лабрадорит"),
    22: ("♄+♃ Мастер", "Под покровительством великих.", "Турмалин, золото"),
    33: ("♀+♆ Высшее", "Любовь + мистика.", "Розовый турмалин, жемчуг"),
}

LUCKY_INFO = {
    1: {"days":"Вс, Пн", "colors":"Золотой, оранжевый", "numbers":"1, 10, 19, 28", "stones":"Рубин, гранат", "time":"9:00–11:00"},
    2: {"days":"Пн, Пт", "colors":"Белый, голубой", "numbers":"2, 11, 20, 29", "stones":"Жемчуг, лунный камень", "time":"20:00–22:00"},
    3: {"days":"Чт, Вт", "colors":"Фиолетовый, жёлтый", "numbers":"3, 12, 21, 30", "stones":"Аметист, топаз", "time":"12:00–14:00"},
    4: {"days":"Сб, Вс", "colors":"Синий, серый", "numbers":"4, 13, 22, 31", "stones":"Сапфир, оникс", "time":"8:00–10:00"},
    5: {"days":"Ср, Пт", "colors":"Зелёный, бирюзовый", "numbers":"5, 14, 23", "stones":"Изумруд, агат", "time":"14:00–16:00"},
    6: {"days":"Пт, Ср", "colors":"Розовый, зелёный", "numbers":"6, 15, 24", "stones":"Изумруд, розовый кварц", "time":"18:00–20:00"},
    7: {"days":"Пн, Вс", "colors":"Фиолетовый, белый", "numbers":"7, 16, 25", "stones":"Аметист, хрусталь", "time":"0:00–2:00"},
    8: {"days":"Сб, Чт", "colors":"Чёрный, золотой", "numbers":"8, 17, 26", "stones":"Сапфир, обсидиан", "time":"10:00–12:00"},
    9: {"days":"Вт, Чт", "colors":"Красный, пурпурный", "numbers":"9, 18, 27", "stones":"Рубин, коралл", "time":"21:00–23:00"},
    11: {"days":"Пн, Вс", "colors":"Серебряный, фиолетовый", "numbers":"11, 22, 33", "stones":"Лабрадорит, опал", "time":"3:00–5:00"},
    22: {"days":"Сб, Чт", "colors":"Золотой, чёрный", "numbers":"22, 4, 8", "stones":"Обсидиан, золото", "time":"11:00–13:00"},
    33: {"days":"Пт, Пн", "colors":"Розовый, золотой", "numbers":"33, 6, 9", "stones":"Турмалин, жемчуг", "time":"16:00–18:00"},
}

NAME_NUMBER_INFO = {
    1: ("Имя Лидера 👑", "Ваше имя несёт энергию первопроходца. Люди тянутся к вам как к авторитету.", "Притягивает уважение и власть."),
    2: ("Имя Дипломата 🕊", "Ваше имя излучает мягкость и располагает к доверию.", "Открывает закрытые сердца."),
    3: ("Имя Артиста 🎭", "Ваше имя несёт творческую вибрацию — вас запоминают.", "Создаёт яркое первое впечатление."),
    4: ("Имя Строителя 🏗", "Ваше имя внушает надёжность.", "Вам доверяют серьёзные дела."),
    5: ("Имя Авантюриста 🌍", "Ваше имя несёт вибрацию свободы.", "Притягивает интересные знакомства."),
    6: ("Имя Хранителя 🏠", "Ваше имя излучает тепло и заботу.", "Люди чувствуют себя в безопасности."),
    7: ("Имя Мудреца 🔮", "Ваше имя несёт вибрацию тайны.", "Притягивает ищущих смысл."),
    8: ("Имя Властелина 💎", "Ваше имя звучит как успех.", "Открывает двери в большой бизнес."),
    9: ("Имя Гуманиста 🌊", "Ваше имя несёт мудрость.", "Вдохновляет и исцеляет."),
    11: ("Имя Провидца ⚡", "Редкое мастер-имя. Вы замечены судьбой.", "Харизма духовного лидера."),
    22: ("Имя Архитектора 🏛", "Мастер-имя строителя реальности.", "Притягивает масштабные проекты."),
    33: ("Имя Учителя 💝", "Высшее мастер-имя. Носить его — миссия.", "Исцеляет одним звуком."),
}

# ─── РАБОТА С ПРОФИЛЕМ ПОЛЬЗОВАТЕЛЯ ─────────────────────────────────────────

def get_profile(uid: int) -> dict:
    return user_profiles.get(uid, {})

def save_profile(uid: int, **kwargs):
    if uid not in user_profiles:
        user_profiles[uid] = {}
    user_profiles[uid].update(kwargs)

def has_birth_date(uid: int) -> bool:
    p = get_profile(uid)
    return "birth_date" in p

def has_name(uid: int) -> bool:
    p = get_profile(uid)
    return "name" in p

def get_number(uid: int) -> int | None:
    p = get_profile(uid)
    if "destiny_number" in p:
        return p["destiny_number"]
    if "birth_date" in p:
        return calc_destiny(date.fromisoformat(p["birth_date"]))
    return None

def get_birth_date(uid: int) -> date | None:
    p = get_profile(uid)
    if "birth_date" in p:
        return date.fromisoformat(p["birth_date"])
    return None

# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────

def main_keyboard() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("🔮 Моё число судьбы"),
        types.KeyboardButton("💑 Совместимость"),
    )
    kb.add(
        types.KeyboardButton("📛 Число имени"),
        types.KeyboardButton("📅 Личный год"),
    )
    kb.add(
        types.KeyboardButton("🌙 Сегодняшний день"),
        types.KeyboardButton("🎯 Скрытый талант"),
    )
    kb.add(
        types.KeyboardButton("⚡ Прошлая жизнь"),
        types.KeyboardButton("☯️ Кармический урок"),
    )
    kb.add(
        types.KeyboardButton("🪐 Планета"),
        types.KeyboardButton("🔮 Чакра"),
    )
    kb.add(
        types.KeyboardButton("🍀 Талисманы"),
        types.KeyboardButton("💎 Число души"),
    )
    kb.add(types.KeyboardButton("🌟 Все мои числа"))
    return kb


def after_result_keyboard(context: str, number: int = 0) -> types.InlineKeyboardMarkup:
    """Умное меню после результата — предлагает то, что ещё не смотрел."""
    kb = types.InlineKeyboardMarkup(row_width=1)

    buy_btn = None
    if context == "destiny":
        buy_btn = types.InlineKeyboardButton(
            f"📄 Полный PDF-отчёт ({PRICE_FULL_REPORT} ⭐) — всё в одном",
            callback_data=f"buy:destiny:{number}")
    elif context == "compat":
        buy_btn = types.InlineKeyboardButton(
            f"💎 Детальный разбор пары ({PRICE_COMPAT_REPORT} ⭐)",
            callback_data="buy:compat:0")
    elif context == "name":
        buy_btn = types.InlineKeyboardButton(
            f"📛 Полный разбор имени ({PRICE_NAME_REPORT} ⭐)",
            callback_data=f"buy:name:{number}")
    elif context == "year":
        buy_btn = types.InlineKeyboardButton(
            f"📅 Прогноз по месяцам ({PRICE_YEAR_REPORT} ⭐)",
            callback_data=f"buy:year:{number}")
    elif context == "karma":
        buy_btn = types.InlineKeyboardButton(
            f"☯️ Полный кармический разбор ({PRICE_KARMA} ⭐)",
            callback_data=f"buy:karma:{number}")

    explore_btns = [
        types.InlineKeyboardButton("🎯 Скрытый талант", callback_data="show:talent"),
        types.InlineKeyboardButton("⚡ Прошлая жизнь", callback_data="show:pastlife"),
        types.InlineKeyboardButton("☯️ Кармический урок", callback_data="show:karma"),
        types.InlineKeyboardButton("🌙 Мой день сегодня", callback_data="show:today"),
        types.InlineKeyboardButton("🪐 Планета-покровитель", callback_data="show:planet"),
        types.InlineKeyboardButton("🔮 Моя чакра", callback_data="show:chakra"),
        types.InlineKeyboardButton("🍀 Талисманы удачи", callback_data="show:lucky"),
        types.InlineKeyboardButton("💎 Число моей души", callback_data="show:soul"),
        types.InlineKeyboardButton("💑 Совместимость с партнёром", callback_data="ask:compat"),
        types.InlineKeyboardButton("🌟 Все мои числа сразу", callback_data="show:all"),
    ]

    # Убираем кнопку текущего контекста из списка
    context_map = {
        "destiny": "show:destiny", "compat": "ask:compat",
        "talent": "show:talent", "pastlife": "show:pastlife",
        "karma": "show:karma", "today": "show:today",
        "planet": "show:planet", "chakra": "show:chakra",
        "lucky": "show:lucky", "soul": "show:soul",
    }
    current_cb = context_map.get(context, "")
    explore_btns = [b for b in explore_btns if b.callback_data != current_cb]

    # Берём первые 5 из оставшихся
    shown = explore_btns[:5]

    all_btns = []
    if buy_btn:
        all_btns.append(buy_btn)
    all_btns.extend(shown)
    all_btns.append(types.InlineKeyboardButton(
        "📲 Поделиться с другом",
        switch_inline_query="🔮 Узнай своё число судьбы бесплатно!"
    ))

    kb.add(*all_btns)
    return kb

# ─── ОБРАБОТЧИКИ КОМАНД ───────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def handle_start(message: types.Message):
    uid  = message.from_user.id
    name = message.from_user.first_name or "друг"
    p    = get_profile(uid)

    if has_birth_date(uid):
        # Уже знаем пользователя — персональное приветствие
        number = get_number(uid)
        info   = DATA["destiny_numbers"].get(str(number), {})
        text = (
            f"🌟 *С возвращением, {name}!*\n\n"
            f"Ваше число судьбы: *{number}* — _{info.get('short','')}_\n\n"
            "Что исследуем сегодня?"
        )
    else:
        text = (
            f"✨ *Привет, {name}!*\n\n"
            "Я — нумерологический оракул.\n\n"
            "Для начала мне нужна ваша *дата рождения*.\n"
            "Введите её в любом формате:\n"
            "`15.03.1990` или `15/03/1990` или `15031990` или `15 марта 1990`"
            + DISCLAIMER
        )
        user_states[uid] = {"step": "first_date"}

    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())

@bot.message_handler(commands=["help"])
def handle_help(message: types.Message):
    bot.send_message(message.chat.id,
        "🔮 *Все возможности:*\n\n"
        "• Число судьбы • Число имени • Число души\n"
        "• Совместимость • Личный год/месяц/день\n"
        "• Планета • Чакра • Талисманы\n"
        "• Скрытый талант • Прошлая жизнь\n"
        "• Кармический урок • Все числа сразу\n\n"
        "Просто нажмите кнопку в меню 👇",
        reply_markup=main_keyboard()
    )
@bot.message_handler(commands=["pay"])
def test_pay(message: types.Message):
    try:
        bot.send_invoice(
            chat_id=message.chat.id,
            title="Тестовый платёж",
            description="Проверка работы Telegram Stars",
            payload="test_payload",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice("Тест", 1)],
        )
        print("✅ Тестовый инвойс отправлен")
    except Exception as e:
        print(f"❌ Ошибка инвойса: {e}")
        bot.send_message(message.chat.id, f"Ошибка: {e}")
# ─── МЕНЮ ─────────────────────────────────────────────────────────────────────

MENU_MAP = {
    "🔮 Моё число судьбы":   "destiny",
    "💑 Совместимость":       "compat",
    "📛 Число имени":         "name",
    "📅 Личный год":          "year",
    "🌙 Сегодняшний день":    "today",
    "🎯 Скрытый талант":      "talent",
    "⚡ Прошлая жизнь":       "pastlife",
    "☯️ Кармический урок":    "karma",
    "🪐 Планета":             "planet",
    "🔮 Чакра":               "chakra",
    "🍀 Талисманы":           "lucky",
    "💎 Число души":          "soul",
    "🌟 Все мои числа":       "all",
}

@bot.message_handler(func=lambda m: m.text in MENU_MAP)
def handle_menu(message: types.Message):
    uid    = message.from_user.id
    action = MENU_MAP[message.text]
    _dispatch_action(message.chat.id, uid, action)


def _dispatch_action(chat_id: int, uid: int, action: str):
    """Центральный диспетчер всех действий."""

    # Если нет даты — сначала спрашиваем её
    if action not in ("compat", "name", "soul") and not has_birth_date(uid):
        user_states[uid] = {"step": "first_date", "pending_action": action}
        bot.send_message(chat_id,
            "Сначала введите вашу дату рождения в любом формате:\n"
            "`15.03.1990` или `15031990` или `15 марта 1990`")
        return

    if action == "destiny":
        _show_destiny(chat_id, uid)
    elif action == "compat":
        _start_compat(chat_id, uid)
    elif action == "name":
        _ask_name(chat_id, uid)
    elif action == "year":
        _show_year(chat_id, uid)
    elif action == "today":
        _show_today(chat_id, uid)
    elif action == "talent":
        _show_talent(chat_id, uid)
    elif action == "pastlife":
        _show_pastlife(chat_id, uid)
    elif action == "karma":
        _show_karma(chat_id, uid)
    elif action == "planet":
        _show_planet(chat_id, uid)
    elif action == "chakra":
        _show_chakra(chat_id, uid)
    elif action == "lucky":
        _show_lucky(chat_id, uid)
    elif action == "soul":
        if not has_name(uid):
            user_states[uid] = {"step": "name", "pending_action": "soul"}
            bot.send_message(chat_id, "📛 Введите ваше *полное имя* для расчёта числа души:")
        else:
            _show_soul(chat_id, uid)
    elif action == "all":
        _show_all(chat_id, uid)

# ─── CALLBACK ─────────────────────────────────────────────────────────────────

@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call: types.CallbackQuery):
    uid = call.from_user.id
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    d = call.data

    if d.startswith("show:"):
        action = d.split(":")[1]
        _dispatch_action(cid, uid, action)

    elif d.startswith("ask:"):
        action = d.split(":")[1]
        if action == "compat":
            _start_compat(cid, uid)

    elif d.startswith("buy:"):
        _, rtype, num = d.split(":")
        _send_invoice(cid, uid, rtype)

# ─── ПОКАЗ РЕЗУЛЬТАТОВ ────────────────────────────────────────────────────────

def _show_destiny(chat_id: int, uid: int):
    bdate  = get_birth_date(uid)
    number = calc_destiny(bdate)
    info   = DATA["destiny_numbers"].get(str(number), {})
    save_profile(uid, destiny_number=number)

    text = (
        f"🔮 *Число вашей судьбы: {number}*\n\n"
        f"_{info.get('short','')}_\n\n"
        f"{info.get('description','')}\n\n"
        f"💪 *Сильные стороны:*\n"
        + "\n".join(f"• {s}" for s in info.get("strengths",[]))
        + "\n\n_Хотите узнать что скрыто глубже?_ 👇"
        + DISCLAIMER
    )
    bot.send_message(chat_id, text)

    # Случайный крючок
    hooks = [
        f"🤫 *Psst...* В вашем числе {number} есть кое-что, о чём большинство не догадывается.",
        f"✨ Число {number} несёт *скрытый талант*, который вы, возможно, ещё не раскрыли.",
        f"🔑 Знаете ли вы, кем были в прошлой жизни? Число {number} помнит всё.",
    ]
    bot.send_message(chat_id, random.choice(hooks),
                     reply_markup=after_result_keyboard("destiny", number))


def _show_today(chat_id: int, uid: int):
    bdate  = get_birth_date(uid)
    number = get_number(uid)
    pd_num = calc_personal_day(bdate)
    pm_num = calc_personal_month(bdate)
    py_num = calc_personal_year(bdate)
    today  = datetime.now()

    affirmations = DAILY_AFFIRMATIONS.get(number, ["Вы на правильном пути."])
    affirmation  = random.choice(affirmations)
    warning      = DAILY_WARNINGS.get(number, "")

    text = (
        f"🌙 *Ваш нумерологический день*\n"
        f"_{today.strftime('%d %B %Y')}_\n\n"
        f"📅 Личный год: *{py_num}* · Месяц: *{pm_num}* · День: *{pd_num}*\n\n"
        f"✨ *Аффирмация дня:*\n_{affirmation}_\n\n"
        f"{warning}\n\n"
        f"💡 *Энергия числа {pd_num} сегодня:* "
        + PERSONAL_YEAR_INFO.get(pd_num, ("","Особый день.","",""))[1]
        + DISCLAIMER
    )
    bot.send_message(chat_id, text,
                     reply_markup=after_result_keyboard("today", number))


def _show_talent(chat_id: int, uid: int):
    number = get_number(uid)
    talent = SECRET_TALENTS.get(number, "🎯 Ваш скрытый талант уникален и ждёт раскрытия.")

    # Интрига в два сообщения
    bot.send_message(chat_id,
        f"🎯 *Скрытый талант числа {number}*\n\n"
        f"Большинство людей с вашим числом так и не узнают об этом...\n\n"
        f"{talent}"
        + DISCLAIMER)
    bot.send_message(chat_id,
        "🔑 *Хотите знать, как активировать этот талант?*\n"
        "Это в полном PDF-отчёте — с конкретными практиками и упражнениями.",
        reply_markup=after_result_keyboard("talent", number))


def _show_pastlife(chat_id: int, uid: int):
    number  = get_number(uid)
    pl_hint = PAST_LIFE_HINTS.get(number, "Ваша прошлая жизнь хранит великие тайны.")

    bot.send_message(chat_id,
        f"⚡ *Прошлая жизнь числа {number}*\n\n"
        f"{pl_hint}\n\n"
        f"_Это объясняет многое в вашей нынешней жизни, не правда ли?_"
        + DISCLAIMER)
    bot.send_message(chat_id,
        "🌀 *Но это лишь намёк...*\n"
        "Полный кармический разбор раскрывает все прошлые жизни, незакрытые долги и дары.",
        reply_markup=after_result_keyboard("pastlife", number))


def _show_karma(chat_id: int, uid: int):
    bdate   = get_birth_date(uid)
    number  = get_number(uid)
    knum    = calc_karma_number(bdate)
    lesson  = KARMA_LESSONS.get(knum, KARMA_LESSONS.get(number, "Ваш кармический путь уникален."))

    bot.send_message(chat_id,
        f"☯️ *Кармическое число: {knum}*\n\n"
        f"{lesson}\n\n"
        f"_Кармические уроки повторяются в каждой жизни, пока не будут усвоены._"
        + DISCLAIMER)
    bot.send_message(chat_id,
        "🔮 *Хотите узнать, как закрыть кармический долг?*\n"
        "Полный кармический разбор — конкретные практики для каждого урока.",
        reply_markup=after_result_keyboard("karma", number))


def _show_year(chat_id: int, uid: int):
    bdate  = get_birth_date(uid)
    number = get_number(uid)
    py     = calc_personal_year(bdate)
    info   = PERSONAL_YEAR_INFO.get(py, ("","","",""))

    bot.send_message(chat_id,
        f"📅 *Личный год {datetime.now().year}: число {py}*\n\n"
        f"*{info[0]}*\n\n{info[1]}\n\n"
        f"✅ *Что делать:* {info[2]}\n\n"
        f"⚠️ *Чего избегать:* {info[3]}"
        + DISCLAIMER)
    bot.send_message(chat_id,
        f"📆 *Хотите прогноз по каждому месяцу {datetime.now().year}?*\n"
        "Лучшие периоды для денег, любви и карьеры — в PDF-отчёте.",
        reply_markup=after_result_keyboard("year", py))


def _show_planet(chat_id: int, uid: int):
    number = get_number(uid)
    info   = PLANET_BY_NUMBER.get(number, ("🌌","Особая планета",""))
    planet, desc, stones = info
    bot.send_message(chat_id,
        f"🪐 *Планета числа {number}: {planet}*\n\n{desc}\n\n💎 *Камни:* {stones}"
        + DISCLAIMER,
        reply_markup=after_result_keyboard("planet", number))


def _show_chakra(chat_id: int, uid: int):
    number = get_number(uid)
    info   = CHAKRA_BY_NUMBER.get(number, ("","",""))
    chakra, desc, stones = info
    bot.send_message(chat_id,
        f"🔮 *Чакра числа {number}: {chakra}*\n\n{desc}\n\n💎 *Камни:* {stones}"
        + DISCLAIMER,
        reply_markup=after_result_keyboard("chakra", number))


def _show_lucky(chat_id: int, uid: int):
    number = get_number(uid)
    info   = LUCKY_INFO.get(number, {})
    bot.send_message(chat_id,
        f"🍀 *Талисманы числа {number}:*\n\n"
        f"📅 Счастливые дни: *{info.get('days','')}*\n"
        f"🎨 Ваши цвета: *{info.get('colors','')}*\n"
        f"⏰ Лучшее время: *{info.get('time','')}*\n"
        f"🔢 Счастливые числа: *{info.get('numbers','')}*\n"
        f"💎 Камни-талисманы: *{info.get('stones','')}*"
        + DISCLAIMER,
        reply_markup=after_result_keyboard("lucky", number))


def _show_soul(chat_id: int, uid: int):
    p      = get_profile(uid)
    name   = p.get("name", "")
    number = calc_soul_number(name)
    pnum   = calc_personality_number(name)

    bot.send_message(chat_id,
        f"💎 *Число души «{name}»: {number}*\n\n"
        f"Число души — это то, чего вы хотите в глубине сердца, ваши истинные желания.\n\n"
        f"_Ваша душа стремится к: {DATA['destiny_numbers'].get(str(number),{}).get('short','уникальному пути')}_\n\n"
        f"🎭 *Число личности: {pnum}*\n"
        f"Это то, каким вас видят другие люди со стороны.\n\n"
        f"_Образ для мира: {DATA['destiny_numbers'].get(str(pnum),{}).get('short','особый образ')}_"
        + DISCLAIMER,
        reply_markup=after_result_keyboard("soul", number))


def _show_all(chat_id: int, uid: int):
    bdate  = get_birth_date(uid)
    number = calc_destiny(bdate)
    p      = get_profile(uid)
    name   = p.get("name", None)

    lines = [
        f"🌟 *Все ваши числа*\n",
        f"🔮 Число судьбы: *{number}* — {DATA['destiny_numbers'].get(str(number),{}).get('short','')}",
        f"📅 Личный год: *{calc_personal_year(bdate)}*",
        f"🌙 Личный месяц: *{calc_personal_month(bdate)}*",
        f"☀️ Личный день: *{calc_personal_day(bdate)}*",
        f"☯️ Кармическое число: *{calc_karma_number(bdate)}*",
        f"🪐 Планета: *{PLANET_BY_NUMBER.get(number,('?','',''))[0]}*",
        f"🔮 Чакра: *{CHAKRA_BY_NUMBER.get(number,('?','',''))[0]}*",
    ]
    if name:
        sn = calc_soul_number(name)
        pn = calc_personality_number(name)
        nn = calc_name_number(name)
        lines += [
            f"📛 Число имени «{name}»: *{nn}*",
            f"💎 Число души: *{sn}*",
            f"🎭 Число личности: *{pn}*",
        ]
    else:
        lines.append("\n_Введите имя чтобы узнать число имени и души_")

    bot.send_message(chat_id, "\n".join(lines) + DISCLAIMER,
                     reply_markup=after_result_keyboard("all", number))


# ─── СОВМЕСТИМОСТЬ ────────────────────────────────────────────────────────────

def _start_compat(chat_id: int, uid: int):
    if has_birth_date(uid):
        # Дату первого партнёра уже знаем — спрашиваем только вторую
        bdate  = get_birth_date(uid)
        number = calc_destiny(bdate)
        user_states[uid] = {"step": "compat_p2", "date1": bdate.isoformat()}
        bot.send_message(chat_id,
            f"💑 *Совместимость*\n\n"
            f"Ваше число: *{number}* ✓\n\n"
            f"Теперь введите дату рождения *партнёра* в любом формате:\n"
            f"`15.03.1990` или `15031990` или `15 марта 1990`")
    else:
        user_states[uid] = {"step": "compat_p1"}
        bot.send_message(chat_id,
            "💑 Введите *вашу* дату рождения в любом формате:")


def _show_compat_result(chat_id: int, uid: int, bdate1: date, bdate2: date):
    n1   = calc_destiny(bdate1)
    n2   = calc_destiny(bdate2)
    key  = f"{min(n1,n2)}-{max(n1,n2)}"
    info = DATA["compatibility"].get(key, {
        "percent":55,"short":"Уникальная пара",
        "love":"Особая динамика.","conflict":"Различие темпераментов",
        "solution":"Открытый диалог","animal":"Загадочное существо"
    })
    pct   = info.get("percent", 55)
    heart = "❤️‍🔥" if pct>=80 else ("💚" if pct>=60 else "💛")

    save_profile(uid, last_n1=n1, last_n2=n2,
                 last_date1=bdate1.isoformat(), last_date2=bdate2.isoformat())

    bot.send_message(chat_id,
        f"💑 *Совместимость: {pct}%* {heart}\n\n"
        f"Числа: *{n1}* и *{n2}* — _{info.get('short','')}_\n\n"
        f"❤️ *В любви:* {info.get('love','')}\n\n"
        f"⚡ *Конфликт:* {info.get('conflict','')}\n\n"
        f"🌿 *Решение:* {info.get('solution','')}\n\n"
        f"🦁 *Тотем пары:* {info.get('animal','')}"
        + DISCLAIMER)

    hooks = [
        "🤫 Детальный разбор раскроет *самое важное* — то, что разрушает именно вашу пару.",
        "🔮 Нумерология видит в вашей паре кое-что неожиданное. Узнать?",
        f"💫 {pct}% — это средний показатель. А вот *потенциальный* процент вас удивит.",
    ]
    bot.send_message(chat_id, random.choice(hooks),
                     reply_markup=after_result_keyboard("compat"))


def _ask_name(chat_id: int, uid: int, pending: str = None):
    user_states[uid] = {"step": "name", "pending_action": pending}
    bot.send_message(chat_id,
        "📛 Введите *имя* (или полное имя) на русском или английском:\n\n"
        "Например: `Анна` · `Анна Иванова` · `Anna`")

# ─── ОСНОВНОЙ ОБРАБОТЧИК ТЕКСТА ──────────────────────────────────────────────

@bot.message_handler(func=lambda m: True)
def handle_text(message: types.Message):
    uid   = message.from_user.id
    state = user_states.get(uid, {})
    step  = state.get("step", "")
    text  = message.text.strip()

    # ── Первое знакомство ────────────────────────────────────────────────────
    if step == "first_date":
        bdate = smart_parse_date(text)
        if not bdate or bdate > date.today():
            bot.send_message(message.chat.id,
                "🤔 Не смог распознать дату. Попробуйте:\n"
                "`15.03.1990` · `15/03/1990` · `15031990` · `15 марта 1990`")
            return
        save_profile(uid, birth_date=bdate.isoformat())
        number = calc_destiny(bdate)
        save_profile(uid, destiny_number=number)
        info = DATA["destiny_numbers"].get(str(number), {})
        pending = state.get("pending_action")

        bot.send_message(message.chat.id,
            f"✨ *Сохранено! Дата: {bdate.strftime('%d.%m.%Y')}*\n\n"
            f"🔮 Ваше число судьбы: *{number}*\n"
            f"_{info.get('short','')}_\n\n"
            "Теперь я знаю вашу дату и больше не буду спрашивать. "
            "Просто нажимайте любую кнопку! 👇",
            reply_markup=main_keyboard())

        user_states.pop(uid, None)

        if pending:
            _dispatch_action(message.chat.id, uid, pending)
        else:
            _show_destiny(message.chat.id, uid)
        return

    # ── Имя ──────────────────────────────────────────────────────────────────
    elif step == "name":
        name = smart_parse_name(text)
        if not name:
            bot.send_message(message.chat.id, "🤔 Введите имя буквами.")
            return
        save_profile(uid, name=name)
        pending = state.get("pending_action")
        user_states.pop(uid, None)

        bot.send_message(message.chat.id, f"✅ *Имя «{name}» сохранено!*")

        if pending == "soul":
            _show_soul(message.chat.id, uid)
        else:
            _show_name_number(message.chat.id, uid)
        return

    # ── Совместимость — дата партнёра 1 ─────────────────────────────────────
    elif step == "compat_p1":
        bdate = smart_parse_date(text)
        if not bdate or bdate > date.today():
            bot.send_message(message.chat.id,
                "🤔 Не смог распознать. Попробуйте: `15.03.1990`")
            return
        user_states[uid] = {"step": "compat_p2", "date1": bdate.isoformat()}
        save_profile(uid, birth_date=bdate.isoformat(),
                     destiny_number=calc_destiny(bdate))
        bot.send_message(message.chat.id,
            f"✅ *{bdate.strftime('%d.%m.%Y')}* принято!\n\n"
            "Теперь дата рождения *партнёра*:")
        return

    # ── Совместимость — дата партнёра 2 ─────────────────────────────────────
    elif step == "compat_p2":
        bdate2 = smart_parse_date(text)
        if not bdate2 or bdate2 > date.today():
            bot.send_message(message.chat.id,
                "🤔 Не смог распознать. Попробуйте: `15.03.1990`")
            return
        bdate1 = date.fromisoformat(state["date1"])
        user_states.pop(uid, None)
        _show_compat_result(message.chat.id, uid, bdate1, bdate2)
        return

    # ── Неизвестный ввод ─────────────────────────────────────────────────────
    else:
        # Попробуем угадать — может пользователь просто вводит дату
        bdate = smart_parse_date(text)
        if bdate and bdate <= date.today():
            save_profile(uid, birth_date=bdate.isoformat(),
                         destiny_number=calc_destiny(bdate))
            bot.send_message(message.chat.id,
                f"🔮 Нашёл дату: *{bdate.strftime('%d.%m.%Y')}*! Считаю число судьбы...")
            _show_destiny(message.chat.id, uid)
            return

        # Может быть имя?
        name = smart_parse_name(text)
        if name and len(name) >= 2 and not any(c.isdigit() for c in name):
            save_profile(uid, name=name)
            _show_name_number(message.chat.id, uid)
            return

        bot.send_message(message.chat.id,
            "Выберите раздел в меню 👇",
            reply_markup=main_keyboard())


def _show_name_number(chat_id: int, uid: int):
    p      = get_profile(uid)
    name   = p.get("name", "")
    number = calc_name_number(name)
    if number == 0:
        bot.send_message(chat_id, "❌ Не удалось рассчитать. Введите имя буквами.")
        return
    info = NAME_NUMBER_INFO.get(number, ("","",""))
    title, desc, power = info

    bot.send_message(chat_id,
        f"📛 *Число имени «{name}»: {number}*\n\n"
        f"*{title}*\n\n{desc}\n\n✨ *Сила имени:* {power}"
        + DISCLAIMER)
    bot.send_message(chat_id,
        "🔑 *Ваше имя — это не случайность.*\n"
        "Полный разбор покажет как имя влияет на карьеру, отношения и удачу.",
        reply_markup=after_result_keyboard("name", number))

# ─── ОПЛАТА ───────────────────────────────────────────────────────────────────

INVOICE_CONFIGS = {
    "destiny": ("🔮 Полный нумерологический отчёт",
                "PDF 15 стр: все числа, таланты, карьера, год, планета, чакра, кармика.",
                PRICE_FULL_REPORT),
    "compat":  ("💑 Детальный разбор совместимости",
                "PDF: портреты, зоны гармонии, конфликты, тотем, советы.",
                PRICE_COMPAT_REPORT),
    "name":    ("📛 Полный разбор имени",
                "PDF: вибрация, карьера, отношения, число души и личности.",
                PRICE_NAME_REPORT),
    "year":    ("📅 Прогноз личного года по месяцам",
                "PDF: лучшие и сложные периоды, советы на каждый квартал.",
                PRICE_YEAR_REPORT),
    "karma":   ("☯️ Полный кармический разбор",
                "PDF: прошлые жизни, долги, уроки, практики для закрытия кармы.",
                PRICE_KARMA),
    "forecast":("🔭 Прогноз на 3 месяца",
                "PDF: детальный прогноз по дням на 3 месяца вперёд.",
                PRICE_FORECAST),
}

def _send_invoice(chat_id: int, uid: int, rtype: str):
    cfg = INVOICE_CONFIGS.get(rtype, INVOICE_CONFIGS["destiny"])
    bot.send_invoice(
        chat_id=chat_id,
        title=cfg[0],
        description=cfg[1],
        invoice_payload=f"{rtype}_{uid}",  # ← ИСПРАВЛЕНО: invoice_payload
        provider_token=PROVIDER_TOKEN,
        currency="XTR",
        prices=[types.LabeledPrice(cfg[0], cfg[2])],
    )
@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(q): bot.answer_pre_checkout_query(q.id, ok=True)

@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message: types.Message):
    uid     = message.from_user.id
    payload = message.successful_payment.invoice_payload
    p       = get_profile(uid)

    bot.send_message(message.chat.id, "✅ *Оплата принята!* ⭐\nГотовлю PDF-отчёт... 📄")

    rtype = payload.split("_")[0]

    if rtype == "destiny":
        bdate = get_birth_date(uid)
        num   = get_number(uid)
        if bdate and num:
            pdf = _gen_destiny_pdf(bdate, num)
            if pdf:
                bot.send_document(message.chat.id, ("numerology_report.pdf", pdf),
                    caption=f"🔮 Ваш полный отчёт! Число: *{num}*" + DISCLAIMER)

    elif rtype == "compat":
        n1,n2 = p.get("last_n1"), p.get("last_n2")
        d1s,d2s = p.get("last_date1"), p.get("last_date2")
        if all([n1,n2,d1s,d2s]):
            pdf = _gen_compat_pdf(
                date.fromisoformat(d1s), date.fromisoformat(d2s), int(n1), int(n2))
            if pdf:
                bot.send_document(message.chat.id, ("compat_report.pdf", pdf),
                    caption=f"💑 Отчёт: *{n1}* и *{n2}*" + DISCLAIMER)

    num = get_number(uid) or 0
    bot.send_message(message.chat.id,
        "🌟 *Что исследуем дальше?*",
        reply_markup=after_result_keyboard("all", num))

# ─── PDF ──────────────────────────────────────────────────────────────────────

def _gen_destiny_pdf(bdate: date, number: int) -> BytesIO | None:
    if not REPORTLAB_OK: return None
    info   = DATA["destiny_numbers"].get(str(number), {})
    buffer = BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=20*mm, leftMargin=20*mm,
                               topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    T  = ParagraphStyle("T", parent=styles["Heading1"], fontSize=22,
                        textColor=colors.HexColor("#4B0082"), alignment=1)
    H  = ParagraphStyle("H", parent=styles["Heading2"], fontSize=14,
                        textColor=colors.HexColor("#4B0082"), spaceBefore=10, spaceAfter=5)
    B  = ParagraphStyle("B", parent=styles["Normal"], fontSize=11, leading=16)
    BL = ParagraphStyle("BL", parent=B, leftIndent=15, spaceAfter=3)
    D  = ParagraphStyle("D", parent=styles["Normal"], fontSize=8,
                        textColor=colors.grey, alignment=1)
    story = [
        Paragraph("🔮 Полный Нумерологический Отчёт", T),
        Paragraph(f"{bdate.strftime('%d.%m.%Y')} · Число судьбы: {number}", 
                  ParagraphStyle("S",parent=styles["Normal"],fontSize=12,
                                  textColor=colors.HexColor("#6A0DAD"),alignment=1)),
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4B0082")),
        Spacer(1, 8*mm),
    ]
    for stitle, skey in [("Ваше число","short"),("Описание","description")]:
        story += [Paragraph(stitle, H), Paragraph(info.get(skey,""), B)]
    for stitle, skey in [("Сильные стороны","strengths"),("Зоны роста","weaknesses"),("Профессии","careers")]:
        story.append(Paragraph(stitle, H))
        for item in info.get(skey,[]):
            story.append(Paragraph(f"• {item}", BL))
    story += [Paragraph("Главный совет", H),
              Paragraph(f'<i>"{info.get("advice","")}"</i>', B), Spacer(1,5*mm)]

    # Скрытый талант
    story += [Paragraph("Скрытый талант", H),
              Paragraph(SECRET_TALENTS.get(number,""), B)]

    # Прошлая жизнь
    story += [Paragraph("Прошлая жизнь", H),
              Paragraph(PAST_LIFE_HINTS.get(number,""), B)]

    # Планета
    planet, pdesc, pstones = PLANET_BY_NUMBER.get(number,("","",""))
    story += [Paragraph(f"Планета-покровитель: {planet}", H),
              Paragraph(f"{pdesc} Камни: {pstones}", B)]

    # Чакра
    chakra, cdesc, cstones = CHAKRA_BY_NUMBER.get(number,("","",""))
    story += [Paragraph(f"Чакра: {chakra}", H),
              Paragraph(f"{cdesc} Камни: {cstones}", B)]

    # Личный год
    py = calc_personal_year(bdate)
    pyi = PERSONAL_YEAR_INFO.get(py,("","","",""))
    story += [Paragraph(f"Личный год {datetime.now().year}: число {py} — {pyi[0]}", H),
              Paragraph(f"{pyi[1]} Что делать: {pyi[2]}", B)]

    # Талисманы
    lucky = LUCKY_INFO.get(number, {})
    story += [Paragraph("Талисманы удачи", H),
              Paragraph(f"Дни: {lucky.get('days','')} · Цвета: {lucky.get('colors','')} · "
                        f"Время: {lucky.get('time','')} · Камни: {lucky.get('stones','')}", B)]

    story += [Spacer(1,10*mm),
              HRFlowable(width="100%",thickness=1,color=colors.grey),
              Paragraph("В развлекательных целях. Не является научным прогнозом.", D)]
    doc.build(story)
    buffer.seek(0)
    return buffer


def _gen_compat_pdf(d1: date, d2: date, n1: int, n2: int) -> BytesIO | None:
    if not REPORTLAB_OK: return None
    key  = f"{min(n1,n2)}-{max(n1,n2)}"
    info = DATA["compatibility"].get(key, {})
    buffer = BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=20*mm, leftMargin=20*mm,
                               topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    T = ParagraphStyle("T",parent=styles["Heading1"],fontSize=20,
                       textColor=colors.HexColor("#8B0000"),alignment=1)
    H = ParagraphStyle("H",parent=styles["Heading2"],fontSize=14,
                       textColor=colors.HexColor("#8B0000"),spaceBefore=8,spaceAfter=4)
    B = ParagraphStyle("B",parent=styles["Normal"],fontSize=11,leading=16)
    D = ParagraphStyle("D",parent=styles["Normal"],fontSize=8,textColor=colors.grey,alignment=1)
    story = [
        Paragraph("💑 Анализ совместимости", T),
        Paragraph(f"{d1.strftime('%d.%m.%Y')} (число {n1}) + {d2.strftime('%d.%m.%Y')} (число {n2})",
                  ParagraphStyle("S",parent=styles["Normal"],fontSize=12,textColor=colors.grey,alignment=1)),
        HRFlowable(width="100%",thickness=2,color=colors.HexColor("#8B0000")),
        Spacer(1,8*mm),
        Paragraph(f"Совместимость: {info.get('percent',55)}%", H),
        Paragraph(info.get("short",""), B),
    ]
    for title, field in [("В любви","love"),("Конфликт","conflict"),("Решение","solution"),("Тотем пары","animal")]:
        story += [Paragraph(title, H), Paragraph(info.get(field,""), B)]
    for num, lbl in [(n1,"Партнёра 1"),(n2,"Партнёра 2")]:
        pi = DATA["destiny_numbers"].get(str(num),{})
        story += [Paragraph(f"Портрет {lbl} (число {num})", H), Paragraph(pi.get("description",""), B)]
    story += [Spacer(1,10*mm),
              HRFlowable(width="100%",thickness=1,color=colors.grey),
              Paragraph("В развлекательных целях.", D)]
    doc.build(story)
    buffer.seek(0)
    return buffer

# ─── ЗАПУСК ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  🔮 Нумерологический бот v4.0 запущен   ║")
    print("╚══════════════════════════════════════════╝")
    print(f"   ReportLab: {'✅' if REPORTLAB_OK else '❌'}")
    print("   15+ разделов · Умный парсинг · Память профиля")
    print("   Ctrl+C — остановить\n")
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
