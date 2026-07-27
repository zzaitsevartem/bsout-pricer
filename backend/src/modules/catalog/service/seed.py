from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.model.catalog import (
    Brand,
    Color,
    ColorSynonym,
    Device,
    DeviceAlias,
    PartType,
    PartTypeSynonym,
    QualityTier,
    QualityTierSynonym,
    Stopword,
)
from src.modules.categories.model.category import Category
from src.modules.stores.model.store import Store

PART_TYPES: dict[str, tuple[str, list[str]]] = {
    "display": (
        "Дисплей",
        [
            "дисплей",
            "экран",
            "display",
            "lcd",
            "модуль",
            "дисплейный модуль",
            "дисплей в сборе",
            "экран в сборе",
            "модуль в сборе",
        ],
    ),
    "battery": (
        "Аккумулятор",
        [
            "аккумулятор",
            "батарея",
            "акб",
            "battery",
            "аккумуляторная батарея",
            "батарейка",
            "акб оригинал",
        ],
    ),
    "back_cover": (
        "Задняя крышка",
        [
            "задняя крышка",
            "крышка",
            "back cover",
            "задняя панель",
            "крышка аккумулятора",
            "стекло задней крышки",
        ],
    ),
    "charging_port": (
        "Разъём зарядки",
        [
            "разъём зарядки",
            "разъем зарядки",
            "шлейф зарядки",
            "charging port",
            "нижний шлейф",
            "разъем питания",
            "системный разъем",
        ],
    ),
    "camera": (
        "Камера",
        [
            "камера",
            "camera",
            "основная камера",
            "фронтальная камера",
            "задняя камера",
            "стекло камеры",
        ],
    ),
    "glass": (
        "Стекло",
        ["стекло", "защитное стекло", "glass", "стекло дисплея", "переклейка стекла"],
    ),
    "frame": (
        "Рамка",
        ["рамка", "корпус", "frame", "средняя часть", "рамка дисплея", "корпус в сборе"],
    ),
    "speaker": (
        "Динамик",
        [
            "динамик",
            "speaker",
            "спикер",
            "полифонический динамик",
            "слуховой динамик",
            "бузер",
            "buzzer",
        ],
    ),
    "microphone": ("Микрофон", ["микрофон", "microphone", "нижний микрофон", "mic"]),
    "board": (
        "Плата",
        ["плата", "материнская плата", "board", "motherboard", "системная плата", "мат плата"],
    ),
    "flex_cable": ("Шлейф", ["шлейф", "шлейфы", "flex", "flex cable", "межплатный шлейф"]),
    "touchscreen": ("Тачскрин", ["тачскрин", "touchscreen", "сенсор", "тач", "сенсорное стекло"]),
    "sim_tray": ("Лоток SIM", ["лоток sim", "сим лоток", "sim tray", "держатель сим"]),
    "button": ("Кнопка", ["кнопка", "кнопки", "button", "кнопка включения", "кнопка громкости"]),
    "vibro": ("Вибромотор", ["вибромотор", "вибро", "vibro", "вибрация"]),
    "antenna": ("Антенна", ["антенна", "antenna", "антенный модуль"]),
    "backlight": ("Подсветка", ["подсветка", "backlight", "подсветка дисплея"]),
    "charger": ("Зарядное устройство", ["зарядное устройство", "зарядка", "сзу", "charger"]),
    "cable": ("Кабель", ["кабель", "cable", "провод", "usb кабель"]),
}

QUALITY_TIERS: dict[str, tuple[str, int, list[str]]] = {
    "original": (
        "Оригинал",
        0,
        ["оригинал", "orig", "original", "оем оригинал", "ориг", "оригинальный", "org"],
    ),
    "oem_hq": (
        "OEM (высокое качество)",
        1,
        ["oem", "oem hq", "hq", "premium", "премиум", "высокое качество", "aaa", "оем"],
    ),
    "copy": (
        "Копия / аналог",
        2,
        ["копия", "copy", "аналог", "china", "китай", "реплика", "неоригинал", "не оригинал"],
    ),
    "service": (
        "Сервисный",
        3,
        [
            "service",
            "service pack",
            "сервисный",
            "восстановленный",
            "восст",
            "refurbished",
            "сервис пак",
        ],
    ),
    "unknown": ("Не определено", 9, []),
}

BRANDS: dict[str, str] = {
    "Apple": "apple",
    "Samsung": "samsung",
    "Xiaomi": "xiaomi",
    "Huawei": "huawei",
    "Honor": "honor",
    "Realme": "realme",
    "OPPO": "oppo",
    "Vivo": "vivo",
    "Nokia": "nokia",
    "Lenovo": "lenovo",
    "Infinix": "infinix",
    "Tecno": "tecno",
}

DEVICES: list[tuple[str, str, str, list[str]]] = [
    ("Apple", "iPhone 11", "apple-iphone-11", ["iphone 11", "айфон 11", "ip11", "iph 11"]),
    (
        "Apple",
        "iPhone 11 Pro",
        "apple-iphone-11-pro",
        ["iphone 11 pro", "айфон 11 про", "ip11 pro", "iph 11 pro"],
    ),
    (
        "Apple",
        "iPhone 11 Pro Max",
        "apple-iphone-11-pro-max",
        ["iphone 11 pro max", "айфон 11 про макс", "ip11 pro max", "iph 11 pro max"],
    ),
    ("Apple", "iPhone 12", "apple-iphone-12", ["iphone 12", "айфон 12", "ip12", "iph 12"]),
    (
        "Apple",
        "iPhone 12 mini",
        "apple-iphone-12-mini",
        ["iphone 12 mini", "айфон 12 мини", "ip12 mini", "iph 12 mini"],
    ),
    (
        "Apple",
        "iPhone 12 Pro",
        "apple-iphone-12-pro",
        ["iphone 12 pro", "айфон 12 про", "ip12 pro", "iph 12 pro"],
    ),
    (
        "Apple",
        "iPhone 12 Pro Max",
        "apple-iphone-12-pro-max",
        ["iphone 12 pro max", "айфон 12 про макс", "ip12 pro max", "iph 12 pro max"],
    ),
    ("Apple", "iPhone 13", "apple-iphone-13", ["iphone 13", "айфон 13", "ip13", "iph 13"]),
    (
        "Apple",
        "iPhone 13 mini",
        "apple-iphone-13-mini",
        ["iphone 13 mini", "айфон 13 мини", "ip13 mini", "iph 13 mini"],
    ),
    (
        "Apple",
        "iPhone 13 Pro",
        "apple-iphone-13-pro",
        ["iphone 13 pro", "айфон 13 про", "ip13 pro", "iph 13 pro"],
    ),
    (
        "Apple",
        "iPhone 13 Pro Max",
        "apple-iphone-13-pro-max",
        ["iphone 13 pro max", "айфон 13 про макс", "ip13 pro max", "iph 13 pro max"],
    ),
    ("Apple", "iPhone 14", "apple-iphone-14", ["iphone 14", "айфон 14", "ip14", "iph 14"]),
    (
        "Apple",
        "iPhone 14 Plus",
        "apple-iphone-14-plus",
        ["iphone 14 plus", "айфон 14 плюс", "ip14 plus", "iph 14 plus"],
    ),
    (
        "Apple",
        "iPhone 14 Pro",
        "apple-iphone-14-pro",
        ["iphone 14 pro", "айфон 14 про", "ip14 pro", "iph 14 pro"],
    ),
    (
        "Apple",
        "iPhone 14 Pro Max",
        "apple-iphone-14-pro-max",
        ["iphone 14 pro max", "айфон 14 про макс", "ip14 pro max", "iph 14 pro max"],
    ),
    ("Apple", "iPhone 15", "apple-iphone-15", ["iphone 15", "айфон 15", "ip15", "iph 15"]),
    (
        "Apple",
        "iPhone 15 Plus",
        "apple-iphone-15-plus",
        ["iphone 15 plus", "айфон 15 плюс", "ip15 plus", "iph 15 plus"],
    ),
    (
        "Apple",
        "iPhone 15 Pro",
        "apple-iphone-15-pro",
        ["iphone 15 pro", "айфон 15 про", "ip15 pro", "iph 15 pro"],
    ),
    (
        "Apple",
        "iPhone 15 Pro Max",
        "apple-iphone-15-pro-max",
        ["iphone 15 pro max", "айфон 15 про макс", "ip15 pro max", "iph 15 pro max"],
    ),
    (
        "Apple",
        "iPhone SE 2020",
        "apple-iphone-se-2020",
        ["iphone se 2020", "айфон se 2020", "ipse 2020", "iphone se 2"],
    ),
    (
        "Apple",
        "iPhone SE 2022",
        "apple-iphone-se-2022",
        ["iphone se 2022", "айфон se 2022", "ipse 2022", "iphone se 3"],
    ),
    (
        "Samsung",
        "Galaxy A12",
        "samsung-galaxy-a12",
        ["galaxy a12", "самсунг a12", "sm-a125", "гэлакси a12"],
    ),
    (
        "Samsung",
        "Galaxy A13",
        "samsung-galaxy-a13",
        ["galaxy a13", "самсунг a13", "sm-a135", "гэлакси a13"],
    ),
    (
        "Samsung",
        "Galaxy A14",
        "samsung-galaxy-a14",
        ["galaxy a14", "самсунг a14", "sm-a145", "гэлакси a14"],
    ),
    (
        "Samsung",
        "Galaxy A32",
        "samsung-galaxy-a32",
        ["galaxy a32", "самсунг a32", "sm-a325", "гэлакси a32"],
    ),
    (
        "Samsung",
        "Galaxy A52",
        "samsung-galaxy-a52",
        ["galaxy a52", "самсунг a52", "sm-a525", "гэлакси a52"],
    ),
    (
        "Samsung",
        "Galaxy A53",
        "samsung-galaxy-a53",
        ["galaxy a53", "самсунг a53", "sm-a536", "гэлакси a53"],
    ),
    (
        "Samsung",
        "Galaxy A54",
        "samsung-galaxy-a54",
        ["galaxy a54", "самсунг a54", "sm-a546", "гэлакси a54"],
    ),
    (
        "Samsung",
        "Galaxy S21",
        "samsung-galaxy-s21",
        ["galaxy s21", "самсунг s21", "sm-g991", "гэлакси s21"],
    ),
    (
        "Samsung",
        "Galaxy S21 Ultra",
        "samsung-galaxy-s21-ultra",
        ["galaxy s21 ultra", "самсунг s21 ультра", "sm-g998", "гэлакси s21 ultra"],
    ),
    (
        "Samsung",
        "Galaxy S22",
        "samsung-galaxy-s22",
        ["galaxy s22", "самсунг s22", "sm-s901", "гэлакси s22"],
    ),
    (
        "Samsung",
        "Galaxy S22 Ultra",
        "samsung-galaxy-s22-ultra",
        ["galaxy s22 ultra", "самсунг s22 ультра", "sm-s908", "гэлакси s22 ultra"],
    ),
    (
        "Samsung",
        "Galaxy S23",
        "samsung-galaxy-s23",
        ["galaxy s23", "самсунг s23", "sm-s911", "гэлакси s23"],
    ),
    (
        "Samsung",
        "Galaxy S23 Ultra",
        "samsung-galaxy-s23-ultra",
        ["galaxy s23 ultra", "самсунг s23 ультра", "sm-s918", "гэлакси s23 ultra"],
    ),
    (
        "Xiaomi",
        "Redmi Note 9",
        "xiaomi-redmi-note-9",
        ["redmi note 9", "редми ноут 9", "redmi note9", "редми note 9"],
    ),
    (
        "Xiaomi",
        "Redmi Note 10",
        "xiaomi-redmi-note-10",
        ["redmi note 10", "редми ноут 10", "redmi note10", "редми note 10"],
    ),
    (
        "Xiaomi",
        "Redmi Note 11",
        "xiaomi-redmi-note-11",
        ["redmi note 11", "редми ноут 11", "redmi note11", "редми note 11"],
    ),
    (
        "Xiaomi",
        "Redmi Note 12",
        "xiaomi-redmi-note-12",
        ["redmi note 12", "редми ноут 12", "redmi note12", "редми note 12"],
    ),
    (
        "Xiaomi",
        "Redmi Note 13",
        "xiaomi-redmi-note-13",
        ["redmi note 13", "редми ноут 13", "redmi note13", "редми note 13"],
    ),
    ("Xiaomi", "Redmi 9A", "xiaomi-redmi-9a", ["redmi 9a", "редми 9a", "xiaomi redmi 9a"]),
    ("Xiaomi", "Redmi 10", "xiaomi-redmi-10", ["redmi 10", "редми 10", "xiaomi redmi 10"]),
    ("Xiaomi", "POCO X3", "xiaomi-poco-x3", ["poco x3", "поко x3", "xiaomi poco x3"]),
    ("Xiaomi", "POCO X5", "xiaomi-poco-x5", ["poco x5", "поко x5", "xiaomi poco x5"]),
    ("Xiaomi", "POCO F5", "xiaomi-poco-f5", ["poco f5", "поко f5", "xiaomi poco f5"]),
    ("Huawei", "P30 Lite", "huawei-p30-lite", ["p30 lite", "хуавей p30 lite", "huawei p30 lite"]),
    ("Huawei", "P40 Lite", "huawei-p40-lite", ["p40 lite", "хуавей p40 lite", "huawei p40 lite"]),
    ("Huawei", "Nova 9", "huawei-nova-9", ["nova 9", "хуавей nova 9", "huawei nova 9"]),
    ("Honor", "Honor 50", "honor-50", ["honor 50", "хонор 50", "honor 50 5g"]),
    ("Honor", "Honor X8", "honor-x8", ["honor x8", "хонор x8", "honor x8 2022"]),
    ("Honor", "Honor 8X", "honor-8x", ["honor 8x", "хонор 8x", "jsn-l21", "honor 8x jsn"]),
    ("Honor", "Honor 9X", "honor-9x", ["honor 9x", "хонор 9x", "honor 9x premium"]),
    ("Realme", "Realme C25", "realme-c25", ["realme c25", "реалми c25", "рилми c25"]),
    ("Realme", "Realme 9 Pro", "realme-9-pro", ["realme 9 pro", "реалми 9 про", "рилми 9 pro"]),
    ("OPPO", "OPPO A54", "oppo-a54", ["oppo a54", "оппо a54", "oppo a54 4g"]),
    ("Vivo", "Vivo Y21", "vivo-y21", ["vivo y21", "виво y21", "vivo y21s"]),
    ("Nokia", "Nokia G21", "nokia-g21", ["nokia g21", "нокиа g21", "нокия g21"]),
    (
        "Lenovo",
        "Lenovo Tab M10",
        "lenovo-tab-m10",
        ["lenovo tab m10", "леново tab m10", "lenovo m10"],
    ),
    ("Apple", "iPhone 5S", "apple-iphone-5s", ["iphone 5s", "айфон 5s", "iphone 5se"]),
    ("Apple", "iPhone 6", "apple-iphone-6", ["iphone 6", "айфон 6", "ip6", "iph 6"]),
    (
        "Apple",
        "iPhone 6 Plus",
        "apple-iphone-6-plus",
        ["iphone 6 plus", "айфон 6 плюс", "ip6 plus"],
    ),
    ("Apple", "iPhone 6S", "apple-iphone-6s", ["iphone 6s", "айфон 6s", "ip6s"]),
    (
        "Apple",
        "iPhone 6S Plus",
        "apple-iphone-6s-plus",
        ["iphone 6s plus", "айфон 6s плюс", "ip6s plus"],
    ),
    ("Apple", "iPhone 7", "apple-iphone-7", ["iphone 7", "айфон 7", "ip7", "iph 7"]),
    (
        "Apple",
        "iPhone 7 Plus",
        "apple-iphone-7-plus",
        ["iphone 7 plus", "айфон 7 плюс", "ip7 plus"],
    ),
    ("Apple", "iPhone 8", "apple-iphone-8", ["iphone 8", "айфон 8", "ip8", "iph 8"]),
    (
        "Apple",
        "iPhone 8 Plus",
        "apple-iphone-8-plus",
        ["iphone 8 plus", "айфон 8 плюс", "ip8 plus"],
    ),
    ("Apple", "iPhone X", "apple-iphone-x", ["iphone x", "айфон x", "ipx", "iph x"]),
    ("Apple", "iPhone XR", "apple-iphone-xr", ["iphone xr", "айфон xr", "ipxr"]),
    ("Apple", "iPhone XS", "apple-iphone-xs", ["iphone xs", "айфон xs", "ipxs"]),
    (
        "Apple",
        "iPhone XS Max",
        "apple-iphone-xs-max",
        ["iphone xs max", "айфон xs макс", "ipxs max"],
    ),
    ("Samsung", "Galaxy J1 2016", "samsung-galaxy-j1-2016", ["j120f", "j1 2016"]),
    ("Samsung", "Galaxy J3 2016", "samsung-galaxy-j3-2016", ["j320f", "j320", "j3 2016"]),
    ("Samsung", "Galaxy J5 2016", "samsung-galaxy-j5-2016", ["j510f", "j5 2016"]),
    ("Samsung", "Galaxy J7 2016", "samsung-galaxy-j7-2016", ["j710f", "j7 2016"]),
    ("Samsung", "Galaxy J4", "samsung-galaxy-j4", ["j400f", "j400", "самсунг j4"]),
    ("Samsung", "Galaxy J7 Neo", "samsung-galaxy-j7-neo", ["j701f", "j700f", "j700", "j7 neo"]),
    ("Samsung", "Galaxy A3 2017", "samsung-galaxy-a3-2017", ["a320f", "a3 2017"]),
    ("Samsung", "Galaxy A5 2017", "samsung-galaxy-a5-2017", ["a520f", "a5 2017"]),
    ("Samsung", "Galaxy A7 2017", "samsung-galaxy-a7-2017", ["a720f", "a7 2017"]),
    ("Samsung", "Galaxy A8 2015", "samsung-galaxy-a8-2015", ["a800f", "a8 2015"]),
    (
        "Samsung",
        "Galaxy A6 Plus 2018",
        "samsung-galaxy-a6-plus-2018",
        ["a605f", "a605fn", "a6+ 2018", "a6 plus 2018"],
    ),
    ("Samsung", "Galaxy A03 Core", "samsung-galaxy-a03-core", ["a032f", "a03 core"]),
    ("Samsung", "Galaxy A10", "samsung-galaxy-a10", ["a105f", "самсунг a10"]),
    ("Samsung", "Galaxy A20", "samsung-galaxy-a20", ["a205f", "самсунг a20"]),
    ("Samsung", "Galaxy A21s", "samsung-galaxy-a21s", ["a217f", "a21s"]),
    ("Samsung", "Galaxy A30", "samsung-galaxy-a30", ["a305f", "самсунг a30"]),
    ("Samsung", "Galaxy A31", "samsung-galaxy-a31", ["a315f", "самсунг a31"]),
    ("Samsung", "Galaxy A50", "samsung-galaxy-a50", ["a505f", "самсунг a50"]),
    ("Samsung", "Galaxy A51", "samsung-galaxy-a51", ["a515f", "самсунг a51"]),
    ("Samsung", "Galaxy S6", "samsung-galaxy-s6", ["g920f", "galaxy s6", "самсунг s6"]),
    ("Samsung", "Galaxy S6 Edge", "samsung-galaxy-s6-edge", ["g925f", "s6 edge"]),
    ("Samsung", "Galaxy S7", "samsung-galaxy-s7", ["g930f", "galaxy s7", "самсунг s7"]),
    ("Samsung", "Galaxy S7 Edge", "samsung-galaxy-s7-edge", ["g935f", "s7 edge"]),
    ("Samsung", "Galaxy S8", "samsung-galaxy-s8", ["g950f", "galaxy s8", "самсунг s8"]),
    ("Samsung", "Galaxy S8 Plus", "samsung-galaxy-s8-plus", ["g955f", "s8 plus"]),
    ("Samsung", "Galaxy S9", "samsung-galaxy-s9", ["g960f", "galaxy s9", "самсунг s9"]),
    ("Samsung", "Galaxy S9 Plus", "samsung-galaxy-s9-plus", ["g965f", "s9 plus"]),
    ("Samsung", "Galaxy S10", "samsung-galaxy-s10", ["g973f", "galaxy s10", "самсунг s10"]),
    ("Samsung", "Galaxy S20", "samsung-galaxy-s20", ["g980f", "galaxy s20", "самсунг s20"]),
    (
        "Xiaomi",
        "Redmi Note 7",
        "xiaomi-redmi-note-7",
        ["redmi note 7", "редми ноут 7", "redmi note7"],
    ),
    (
        "Xiaomi",
        "Redmi Note 8",
        "xiaomi-redmi-note-8",
        ["redmi note 8", "редми ноут 8", "redmi note8"],
    ),
    (
        "Xiaomi",
        "Redmi Note 8 Pro",
        "xiaomi-redmi-note-8-pro",
        ["redmi note 8 pro", "m1906g7", "redmi note8 pro"],
    ),
    ("Xiaomi", "Redmi Note 8T", "xiaomi-redmi-note-8t", ["redmi note 8t", "m1908c3xg"]),
    ("Xiaomi", "Redmi 6", "xiaomi-redmi-6", ["redmi 6", "редми 6"]),
    ("Xiaomi", "Redmi 6A", "xiaomi-redmi-6a", ["redmi 6a", "редми 6a"]),
    ("Xiaomi", "Redmi 8", "xiaomi-redmi-8", ["redmi 8", "редми 8"]),
    ("Xiaomi", "Redmi 8A", "xiaomi-redmi-8a", ["redmi 8a", "редми 8a"]),
    ("Xiaomi", "Redmi 9", "xiaomi-redmi-9", ["redmi 9", "редми 9"]),
    ("Xiaomi", "Redmi 9C", "xiaomi-redmi-9c", ["redmi 9c", "редми 9c"]),
    ("Huawei", "Honor 10 Lite", "huawei-honor-10-lite", ["honor 10 lite", "honor 10i", "hry-lx1"]),
    ("Honor", "Honor 7A", "honor-7a", ["honor 7a", "хонор 7a"]),
    ("Honor", "Honor 7C", "honor-7c", ["honor 7c", "хонор 7c"]),
    ("Honor", "Honor 8A", "honor-8a", ["honor 8a", "хонор 8a"]),
    ("Realme", "Realme C11", "realme-c11", ["realme c11", "рилми c11"]),
    ("Realme", "Realme C20", "realme-c20", ["realme c20", "рилми c20"]),
    ("Realme", "Realme C21", "realme-c21", ["realme c21", "рилми c21"]),
    ("Realme", "Realme 8", "realme-8", ["realme 8", "рилми 8"]),
    ("OPPO", "OPPO A5s", "oppo-a5s", ["oppo a5s", "оппо a5s"]),
    ("OPPO", "OPPO A15", "oppo-a15", ["oppo a15", "оппо a15"]),
    ("Infinix", "Infinix Note 11", "infinix-note-11", ["infinix note 11", "note 11"]),
    ("Infinix", "Infinix Note 12", "infinix-note-12", ["infinix note 12", "note 12"]),
    ("Infinix", "Infinix Hot 11", "infinix-hot-11", ["infinix hot 11", "hot 11"]),
    ("Tecno", "Tecno Spark 8", "tecno-spark-8", ["tecno spark 8", "spark 8"]),
    ("Tecno", "Tecno Spark 10", "tecno-spark-10", ["tecno spark 10", "spark 10"]),
]

COLORS: dict[str, tuple[str, list[str]]] = {
    "black": ("Чёрный", ["чёрный", "черный", "black", "space black", "midnight"]),
    "white": ("Белый", ["белый", "white", "starlight"]),
    "red": ("Красный", ["красный", "red", "product red"]),
    "blue": ("Синий", ["синий", "blue", "голубой", "sierra blue"]),
    "green": ("Зелёный", ["зелёный", "зеленый", "green", "alpine green"]),
    "gold": ("Золотой", ["золотой", "gold", "золото"]),
    "silver": ("Серебристый", ["серебристый", "silver", "серебро"]),
    "gray": ("Серый", ["серый", "gray", "grey", "space gray", "графит", "графитовый"]),
    "purple": ("Фиолетовый", ["фиолетовый", "purple", "сиреневый", "deep purple"]),
    "pink": ("Розовый", ["розовый", "pink", "розовое золото"]),
    "yellow": ("Жёлтый", ["жёлтый", "желтый", "yellow"]),
    "orange": ("Оранжевый", ["оранжевый", "orange", "коралловый"]),
}

STOPWORDS: list[str] = [
    "для",
    "в",
    "на",
    "с",
    "и",
    "от",
    "по",
    "к",
    "у",
    "за",
    "или",
    "а",
    "новый",
    "новая",
    "новое",
    "новые",
    "шт",
    "штука",
    "штук",
    "уп",
    "упаковка",
    "арт",
    "артикул",
    "код",
    "товар",
    "товары",
    "запчасть",
    "запчасти",
    "аксессуары",
    "распродажа",
    "акция",
    "скидка",
    "хит",
    "новинка",
    "продажа",
    "цена",
    "опт",
    "розница",
    "доставка",
    "гарантия",
    "наличие",
    "заказ",
]

STORES: list[tuple[str, str, str]] = [
    ("tgsm", "ТГСМ", "https://taggsm.ru"),
    ("profi", "Профи", "https://siriust.ru"),
    ("liberti", "Либерти", "https://liberti.ru"),
    ("greenspark", "ГринСпарк", "https://green-spark.ru"),
    ("divizion", "Дивизион", "https://divizion126.ru"),
]

CATEGORIES: list[tuple[str, str]] = [
    ("displays", "Дисплеи"),
    ("batteries", "Аккумуляторы"),
    ("body-parts", "Корпусные детали"),
    ("flex-cables", "Шлейфы"),
    ("cameras", "Камеры"),
    ("speakers", "Динамики"),
    ("boards", "Платы"),
]


async def _get_or_create_part_type(db: AsyncSession, code: str, name_ru: str) -> PartType:
    existing = (
        await db.execute(select(PartType).where(PartType.code == code))
    ).scalar_one_or_none()
    if existing:
        return existing
    part_type = PartType(code=code, name_ru=name_ru)
    db.add(part_type)
    await db.flush()
    return part_type


async def _get_or_create_quality_tier(
    db: AsyncSession, code: str, name_ru: str, rank: int
) -> QualityTier:
    existing = (
        await db.execute(select(QualityTier).where(QualityTier.code == code))
    ).scalar_one_or_none()
    if existing:
        return existing
    tier = QualityTier(code=code, name_ru=name_ru, rank=rank)
    db.add(tier)
    await db.flush()
    return tier


async def _get_or_create_brand(db: AsyncSession, name: str, slug: str) -> Brand:
    existing = (await db.execute(select(Brand).where(Brand.name == name))).scalar_one_or_none()
    if existing:
        return existing
    brand = Brand(name=name, slug=slug)
    db.add(brand)
    await db.flush()
    return brand


async def _get_or_create_color(db: AsyncSession, code: str, name_ru: str) -> Color:
    existing = (await db.execute(select(Color).where(Color.code == code))).scalar_one_or_none()
    if existing:
        return existing
    color = Color(code=code, name_ru=name_ru)
    db.add(color)
    await db.flush()
    return color


async def _ensure_synonym(
    db: AsyncSession, model, fk_field: str, parent_id: int, synonym: str
) -> None:
    existing = (
        await db.execute(select(model).where(model.synonym == synonym))
    ).scalar_one_or_none()
    if existing:
        return
    db.add(model(**{fk_field: parent_id, "synonym": synonym}))
    await db.flush()


async def _ensure_device_alias(db: AsyncSession, device_id: int, alias: str) -> None:
    existing = (
        await db.execute(select(DeviceAlias).where(DeviceAlias.alias == alias))
    ).scalar_one_or_none()
    if existing:
        return
    db.add(DeviceAlias(device_id=device_id, alias=alias, source="seed"))
    await db.flush()


async def _ensure_stopword(db: AsyncSession, word: str) -> None:
    existing = (
        await db.execute(select(Stopword).where(Stopword.word == word))
    ).scalar_one_or_none()
    if existing:
        return
    db.add(Stopword(word=word))
    await db.flush()


async def seed_catalog(db: AsyncSession) -> None:
    for code, (name_ru, synonyms) in PART_TYPES.items():
        part_type = await _get_or_create_part_type(db, code, name_ru)
        for synonym in synonyms:
            await _ensure_synonym(db, PartTypeSynonym, "part_type_id", part_type.id, synonym)

    for code, (name_ru, rank, synonyms) in QUALITY_TIERS.items():
        tier = await _get_or_create_quality_tier(db, code, name_ru, rank)
        for synonym in synonyms:
            await _ensure_synonym(db, QualityTierSynonym, "quality_tier_id", tier.id, synonym)

    brands: dict[str, Brand] = {}
    for name, slug in BRANDS.items():
        brands[name] = await _get_or_create_brand(db, name, slug)

    for brand_name, device_name, model_key, aliases in DEVICES:
        brand = brands.get(brand_name)
        if brand is None:
            continue
        device = (
            await db.execute(select(Device).where(Device.model_key == model_key))
        ).scalar_one_or_none()
        if device is None:
            device = Device(brand_id=brand.id, name=device_name, model_key=model_key)
            db.add(device)
            await db.flush()
        for alias in aliases:
            await _ensure_device_alias(db, device.id, alias)

    for code, (name_ru, synonyms) in COLORS.items():
        color = await _get_or_create_color(db, code, name_ru)
        for synonym in synonyms:
            await _ensure_synonym(db, ColorSynonym, "color_id", color.id, synonym)

    for word in STOPWORDS:
        await _ensure_stopword(db, word)


async def seed_stores(db: AsyncSession) -> None:
    for slug, name, website_url in STORES:
        existing = (await db.execute(select(Store).where(Store.slug == slug))).scalar_one_or_none()
        if existing:
            continue
        db.add(Store(slug=slug, name=name, website_url=website_url, is_active=True))
        await db.flush()


async def seed_categories(db: AsyncSession) -> None:
    for slug, name in CATEGORIES:
        existing = (
            await db.execute(select(Category).where(Category.slug == slug))
        ).scalar_one_or_none()
        if existing:
            continue
        db.add(Category(slug=slug, name=name))
        await db.flush()


async def seed_all(db: AsyncSession) -> None:
    await seed_catalog(db)
    await seed_stores(db)
    await seed_categories(db)
