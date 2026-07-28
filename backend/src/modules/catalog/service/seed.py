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
    (
        "Realme",
        "Realme 9 Pro",
        "realme-9-pro",
        ["realme 9 pro", "реалми 9 про", "рилми 9 pro", "realme 9pro", "рилми 9pro"],
    ),
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
    ("Samsung", "Galaxy S8 Plus", "samsung-galaxy-s8-plus", ["g955f", "s8 plus", "s8plus"]),
    ("Samsung", "Galaxy S9", "samsung-galaxy-s9", ["g960f", "galaxy s9", "самсунг s9"]),
    ("Samsung", "Galaxy S9 Plus", "samsung-galaxy-s9-plus", ["g965f", "s9 plus", "s9plus"]),
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
    ("Apple", "iPhone 16", "apple-iphone-16", ["ip16", "iphone 16", "айфон 16"]),
    (
        "Apple",
        "iPhone 16 Plus",
        "apple-iphone-16-plus",
        ["iphone 16 plus", "айфон 16 plus", "iphone 16plus", "айфон 16plus"],
    ),
    (
        "Apple",
        "iPhone 16 Pro",
        "apple-iphone-16-pro",
        ["iphone 16 pro", "айфон 16 pro", "iphone 16pro", "айфон 16pro"],
    ),
    (
        "Apple",
        "iPhone 16 Pro Max",
        "apple-iphone-16-pro-max",
        ["ip16 pro max", "iphone 16 pro max", "айфон 16 pro max"],
    ),
    ("Apple", "iPhone 17", "apple-iphone-17", ["ip17", "iphone 17", "айфон 17"]),
    (
        "Apple",
        "iPhone 17 Pro",
        "apple-iphone-17-pro",
        ["iphone 17 pro", "айфон 17 pro", "iphone 17pro", "айфон 17pro"],
    ),
    (
        "Apple",
        "iPhone 17 Pro Max",
        "apple-iphone-17-pro-max",
        ["ip17 pro max", "iphone 17 pro max", "айфон 17 pro max"],
    ),
    ("Apple", "Watch S2", "apple-watch-s2", ["apple watch s2", "watch s2"]),
    ("Apple", "Watch S3", "apple-watch-s3", ["apple watch s3", "watch s3"]),
    ("Apple", "Watch S4", "apple-watch-s4", ["apple watch s4", "watch s4"]),
    ("Apple", "Watch S5", "apple-watch-s5", ["apple watch s5", "watch s5"]),
    ("Apple", "Watch S6", "apple-watch-s6", ["apple watch s6", "watch s6"]),
    ("Apple", "Watch SE", "apple-watch-se", ["apple watch se", "watch se"]),
    ("Apple", "Watch S7", "apple-watch-s7", ["apple watch s7", "watch s7"]),
    ("Apple", "Watch S8", "apple-watch-s8", ["apple watch s8", "watch s8"]),
    ("Apple", "Watch S9", "apple-watch-s9", ["apple watch s9", "watch s9"]),
    (
        "Samsung",
        "Galaxy S7 Plus",
        "samsung-galaxy-s7-plus",
        ["galaxy s7 plus", "s7 plus", "galaxy s7plus", "s7plus"],
    ),
    (
        "Samsung",
        "Galaxy S7 Ultra",
        "samsung-galaxy-s7-ultra",
        ["galaxy s7 ultra", "s7 ultra", "galaxy s7ultra", "s7ultra"],
    ),
    (
        "Samsung",
        "Galaxy S7 FE",
        "samsung-galaxy-s7-fe",
        ["galaxy s7 fe", "s7 fe", "galaxy s7fe", "s7fe"],
    ),
    (
        "Samsung",
        "Galaxy S8 Ultra",
        "samsung-galaxy-s8-ultra",
        ["galaxy s8 ultra", "s8 ultra", "galaxy s8ultra", "s8ultra"],
    ),
    (
        "Samsung",
        "Galaxy S8 FE",
        "samsung-galaxy-s8-fe",
        ["galaxy s8 fe", "s8 fe", "galaxy s8fe", "s8fe"],
    ),
    (
        "Samsung",
        "Galaxy S9 Ultra",
        "samsung-galaxy-s9-ultra",
        ["galaxy s9 ultra", "s9 ultra", "galaxy s9ultra", "s9ultra"],
    ),
    (
        "Samsung",
        "Galaxy S9 FE",
        "samsung-galaxy-s9-fe",
        ["galaxy s9 fe", "s9 fe", "galaxy s9fe", "s9fe"],
    ),
    (
        "Samsung",
        "Galaxy S10 Plus",
        "samsung-galaxy-s10-plus",
        ["galaxy s10 plus", "s10 plus", "galaxy s10plus", "s10plus"],
    ),
    (
        "Samsung",
        "Galaxy S10 Ultra",
        "samsung-galaxy-s10-ultra",
        ["galaxy s10 ultra", "s10 ultra", "galaxy s10ultra", "s10ultra"],
    ),
    (
        "Samsung",
        "Galaxy S10 FE",
        "samsung-galaxy-s10-fe",
        ["galaxy s10 fe", "s10 fe", "galaxy s10fe", "s10fe"],
    ),
    (
        "Samsung",
        "Galaxy S20 Plus",
        "samsung-galaxy-s20-plus",
        ["galaxy s20 plus", "s20 plus", "galaxy s20plus", "s20plus"],
    ),
    (
        "Samsung",
        "Galaxy S20 Ultra",
        "samsung-galaxy-s20-ultra",
        ["galaxy s20 ultra", "s20 ultra", "galaxy s20ultra", "s20ultra"],
    ),
    (
        "Samsung",
        "Galaxy S20 FE",
        "samsung-galaxy-s20-fe",
        ["galaxy s20 fe", "s20 fe", "galaxy s20fe", "s20fe"],
    ),
    (
        "Samsung",
        "Galaxy S21 Plus",
        "samsung-galaxy-s21-plus",
        ["g996", "galaxy s21 plus", "s21 plus"],
    ),
    (
        "Samsung",
        "Galaxy S21 FE",
        "samsung-galaxy-s21-fe",
        ["galaxy s21 fe", "s21 fe", "galaxy s21fe", "s21fe"],
    ),
    (
        "Samsung",
        "Galaxy S22 Plus",
        "samsung-galaxy-s22-plus",
        ["galaxy s22 plus", "s22 plus", "galaxy s22plus", "s22plus"],
    ),
    (
        "Samsung",
        "Galaxy S22 FE",
        "samsung-galaxy-s22-fe",
        ["galaxy s22 fe", "s22 fe", "galaxy s22fe", "s22fe"],
    ),
    (
        "Samsung",
        "Galaxy S23 Plus",
        "samsung-galaxy-s23-plus",
        ["galaxy s23 plus", "s23 plus", "s916"],
    ),
    (
        "Samsung",
        "Galaxy S23 FE",
        "samsung-galaxy-s23-fe",
        ["galaxy s23 fe", "s23 fe", "galaxy s23fe", "s23fe"],
    ),
    ("Samsung", "Galaxy S24", "samsung-galaxy-s24", ["galaxy s24", "s24"]),
    (
        "Samsung",
        "Galaxy S24 Plus",
        "samsung-galaxy-s24-plus",
        ["galaxy s24 plus", "s24 plus", "galaxy s24plus", "s24plus"],
    ),
    (
        "Samsung",
        "Galaxy S24 Ultra",
        "samsung-galaxy-s24-ultra",
        ["galaxy s24 ultra", "s24 ultra", "galaxy s24ultra", "s24ultra"],
    ),
    (
        "Samsung",
        "Galaxy S24 FE",
        "samsung-galaxy-s24-fe",
        ["galaxy s24 fe", "s24 fe", "galaxy s24fe", "s24fe"],
    ),
    ("Samsung", "Galaxy S25", "samsung-galaxy-s25", ["galaxy s25", "s25", "s931"]),
    (
        "Samsung",
        "Galaxy S25 Plus",
        "samsung-galaxy-s25-plus",
        ["galaxy s25 plus", "s25 plus", "s936"],
    ),
    (
        "Samsung",
        "Galaxy S25 Ultra",
        "samsung-galaxy-s25-ultra",
        ["galaxy s25 ultra", "s25 ultra", "galaxy s25ultra", "s25ultra"],
    ),
    (
        "Samsung",
        "Galaxy S25 FE",
        "samsung-galaxy-s25-fe",
        ["galaxy s25 fe", "s25 fe", "galaxy s25fe", "s25fe"],
    ),
    ("Samsung", "Galaxy S26", "samsung-galaxy-s26", ["galaxy s26", "s26", "s942"]),
    (
        "Samsung",
        "Galaxy S26 Plus",
        "samsung-galaxy-s26-plus",
        ["galaxy s26 plus", "s26 plus", "galaxy s26plus", "s26plus"],
    ),
    (
        "Samsung",
        "Galaxy S26 Ultra",
        "samsung-galaxy-s26-ultra",
        ["galaxy s26 ultra", "s26 ultra", "s948"],
    ),
    (
        "Samsung",
        "Galaxy S26 FE",
        "samsung-galaxy-s26-fe",
        ["galaxy s26 fe", "s26 fe", "galaxy s26fe", "s26fe"],
    ),
    ("Samsung", "Galaxy Note 8", "samsung-galaxy-note-8", ["galaxy note 8", "note 8"]),
    ("Samsung", "Galaxy Note 9", "samsung-galaxy-note-9", ["galaxy note 9", "note 9"]),
    ("Samsung", "Galaxy Note 10", "samsung-galaxy-note-10", ["galaxy note 10", "note 10"]),
    (
        "Samsung",
        "Galaxy Note 10 Plus",
        "samsung-galaxy-note-10-plus",
        ["galaxy note 10 plus", "note 10 plus"],
    ),
    ("Samsung", "Galaxy Note 20", "samsung-galaxy-note-20", ["galaxy note 20", "note 20"]),
    (
        "Samsung",
        "Galaxy Note 20 Ultra",
        "samsung-galaxy-note-20-ultra",
        ["galaxy note 20 ultra", "note 20 ultra"],
    ),
    ("Samsung", "Galaxy A01", "samsung-galaxy-a01", ["a01", "a01 5g", "galaxy a01"]),
    ("Samsung", "Galaxy A02", "samsung-galaxy-a02", ["a02", "a02 5g", "galaxy a02"]),
    ("Samsung", "Galaxy A02S", "samsung-galaxy-a02s", ["a025", "a02s", "a02s 5g", "galaxy a02s"]),
    ("Samsung", "Galaxy A03", "samsung-galaxy-a03", ["a03", "a03 5g", "galaxy a03"]),
    ("Samsung", "Galaxy A03S", "samsung-galaxy-a03s", ["a03s", "a03s 5g", "galaxy a03s"]),
    ("Samsung", "Galaxy A04", "samsung-galaxy-a04", ["a04", "a04 5g", "galaxy a04"]),
    ("Samsung", "Galaxy A04S", "samsung-galaxy-a04s", ["a047", "a04s", "a04s 5g", "galaxy a04s"]),
    ("Samsung", "Galaxy A05", "samsung-galaxy-a05", ["a05", "a05 5g", "galaxy a05"]),
    ("Samsung", "Galaxy A06", "samsung-galaxy-a06", ["a06", "a06 5g", "galaxy a06"]),
    ("Samsung", "Galaxy A07", "samsung-galaxy-a07", ["a07", "a07 5g", "a075", "galaxy a07"]),
    ("Samsung", "Galaxy A11", "samsung-galaxy-a11", ["a11", "a11 5g", "galaxy a11"]),
    ("Samsung", "Galaxy A15", "samsung-galaxy-a15", ["a15", "a15 5g", "galaxy a15"]),
    ("Samsung", "Galaxy A16", "samsung-galaxy-a16", ["a16", "a16 5g", "galaxy a16"]),
    ("Samsung", "Galaxy A21", "samsung-galaxy-a21", ["a21", "a21 5g", "galaxy a21"]),
    ("Samsung", "Galaxy A22", "samsung-galaxy-a22", ["a22", "a22 5g", "a225", "galaxy a22"]),
    ("Samsung", "Galaxy A22S", "samsung-galaxy-a22s", ["a226", "a22s", "a22s 5g", "galaxy a22s"]),
    ("Samsung", "Galaxy A23", "samsung-galaxy-a23", ["a23", "a23 5g", "galaxy a23"]),
    ("Samsung", "Galaxy A24", "samsung-galaxy-a24", ["a24", "a24 5g", "galaxy a24"]),
    ("Samsung", "Galaxy A25", "samsung-galaxy-a25", ["a25", "a25 5g", "galaxy a25"]),
    ("Samsung", "Galaxy A26", "samsung-galaxy-a26", ["a26", "a26 5g", "a266", "galaxy a26"]),
    ("Samsung", "Galaxy A30S", "samsung-galaxy-a30s", ["a307", "a30s", "a30s 5g", "galaxy a30s"]),
    ("Samsung", "Galaxy A33", "samsung-galaxy-a33", ["a33", "a33 5g", "a336", "galaxy a33"]),
    ("Samsung", "Galaxy A34", "samsung-galaxy-a34", ["a34", "a34 5g", "a346", "galaxy a34"]),
    ("Samsung", "Galaxy A35", "samsung-galaxy-a35", ["a35", "a35 5g", "a356", "galaxy a35"]),
    ("Samsung", "Galaxy A36", "samsung-galaxy-a36", ["a36", "a36 5g", "a366", "galaxy a36"]),
    ("Samsung", "Galaxy A55", "samsung-galaxy-a55", ["a55", "a55 5g", "galaxy a55"]),
    ("Samsung", "Galaxy A56", "samsung-galaxy-a56", ["a56", "a56 5g", "galaxy a56"]),
    ("Samsung", "Galaxy A57", "samsung-galaxy-a57", ["a57", "a57 5g", "a576", "galaxy a57"]),
    ("Samsung", "Galaxy A70", "samsung-galaxy-a70", ["a70", "a70 5g", "galaxy a70"]),
    ("Samsung", "Galaxy A71", "samsung-galaxy-a71", ["a71", "a71 5g", "galaxy a71"]),
    ("Samsung", "Galaxy A72", "samsung-galaxy-a72", ["a72", "a72 5g", "galaxy a72"]),
    ("Samsung", "Galaxy A73", "samsung-galaxy-a73", ["a73", "a73 5g", "galaxy a73"]),
    ("Samsung", "Galaxy J3", "samsung-galaxy-j3", ["galaxy j3", "j3"]),
    ("Samsung", "Galaxy J5", "samsung-galaxy-j5", ["galaxy j5", "j5", "j500"]),
    ("Samsung", "Galaxy J6", "samsung-galaxy-j6", ["galaxy j6", "j6"]),
    ("Samsung", "Galaxy J7", "samsung-galaxy-j7", ["galaxy j7", "j7", "j710"]),
    ("Samsung", "Galaxy M12", "samsung-galaxy-m12", ["galaxy m12", "m12"]),
    ("Samsung", "Galaxy M21", "samsung-galaxy-m21", ["galaxy m21", "m21"]),
    ("Samsung", "Galaxy M31", "samsung-galaxy-m31", ["galaxy m31", "m31"]),
    ("Samsung", "Galaxy M32", "samsung-galaxy-m32", ["galaxy m32", "m32"]),
    ("Samsung", "Galaxy M33", "samsung-galaxy-m33", ["galaxy m33", "m33"]),
    ("Xiaomi", "Redmi 9T", "xiaomi-redmi-9t", ["redmi 9t", "redmi9t"]),
    ("Xiaomi", "Redmi 10A", "xiaomi-redmi-10a", ["redmi 10a", "redmi10a"]),
    ("Xiaomi", "Redmi 10C", "xiaomi-redmi-10c", ["redmi 10c", "redmi10c"]),
    ("Xiaomi", "Redmi 11", "xiaomi-redmi-11", ["redmi 11", "redmi11"]),
    ("Xiaomi", "Redmi 12", "xiaomi-redmi-12", ["redmi 12", "redmi12"]),
    ("Xiaomi", "Redmi 12C", "xiaomi-redmi-12c", ["redmi 12c", "redmi12c"]),
    ("Xiaomi", "Redmi 13", "xiaomi-redmi-13", ["redmi 13", "redmi13"]),
    ("Xiaomi", "Redmi 13C", "xiaomi-redmi-13c", ["redmi 13c", "redmi13c"]),
    ("Xiaomi", "Redmi 14", "xiaomi-redmi-14", ["redmi 14", "redmi14"]),
    ("Xiaomi", "Redmi 14C", "xiaomi-redmi-14c", ["redmi 14c", "redmi14c"]),
    ("Xiaomi", "Redmi 15", "xiaomi-redmi-15", ["redmi 15", "redmi15"]),
    (
        "Xiaomi",
        "Redmi Note 9 Pro",
        "xiaomi-redmi-note-9-pro",
        ["note 9 pro", "redmi note 9 pro", "note 9pro", "redmi note 9pro"],
    ),
    (
        "Xiaomi",
        "Redmi Note 10 Pro",
        "xiaomi-redmi-note-10-pro",
        ["note 10 pro", "redmi note 10 pro"],
    ),
    (
        "Xiaomi",
        "Redmi Note 11 Pro",
        "xiaomi-redmi-note-11-pro",
        ["redmi note 11 pro", "xiaomi redmi note 11 pro"],
    ),
    (
        "Xiaomi",
        "Redmi Note 12 Pro",
        "xiaomi-redmi-note-12-pro",
        ["redmi note 12 pro", "xiaomi redmi note 12 pro"],
    ),
    (
        "Xiaomi",
        "Redmi Note 13 Pro",
        "xiaomi-redmi-note-13-pro",
        ["note 13 pro", "redmi note 13 pro"],
    ),
    ("Xiaomi", "Redmi Note 14", "xiaomi-redmi-note-14", ["note 14", "redmi note 14"]),
    (
        "Xiaomi",
        "Redmi Note 14 Pro",
        "xiaomi-redmi-note-14-pro",
        ["note 14 pro", "redmi note 14 pro"],
    ),
    ("Xiaomi", "Redmi Note 15", "xiaomi-redmi-note-15", ["note 15", "redmi note 15"]),
    (
        "Xiaomi",
        "Redmi Note 15 Pro",
        "xiaomi-redmi-note-15-pro",
        ["note 15 pro", "redmi note 15 pro"],
    ),
    (
        "Xiaomi",
        "Redmi Note 15 Pro Plus",
        "xiaomi-redmi-note-15-pro-plus",
        ["note 15 pro plus", "redmi note 15 pro plus"],
    ),
    ("Xiaomi", "POCO X4", "xiaomi-poco-x4", ["poco x4", "pocox4"]),
    ("Xiaomi", "POCO X6", "xiaomi-poco-x6", ["poco x6", "pocox6"]),
    ("Xiaomi", "POCO X7", "xiaomi-poco-x7", ["poco x7", "pocox7"]),
    ("Xiaomi", "POCO M3", "xiaomi-poco-m3", ["poco m3", "pocom3"]),
    ("Xiaomi", "POCO M4", "xiaomi-poco-m4", ["poco m4", "pocom4"]),
    ("Xiaomi", "POCO M5", "xiaomi-poco-m5", ["poco m5", "pocom5"]),
    ("Xiaomi", "POCO M6", "xiaomi-poco-m6", ["poco m6", "pocom6"]),
    ("Xiaomi", "POCO M7", "xiaomi-poco-m7", ["poco m7", "pocom7"]),
    ("Xiaomi", "POCO F3", "xiaomi-poco-f3", ["poco f3", "pocof3"]),
    ("Xiaomi", "POCO F4", "xiaomi-poco-f4", ["poco f4", "pocof4"]),
    ("Xiaomi", "POCO F6", "xiaomi-poco-f6", ["poco f6", "pocof6"]),
    ("Xiaomi", "POCO C40", "xiaomi-poco-c40", ["poco c40", "pococ40"]),
    ("Xiaomi", "POCO C65", "xiaomi-poco-c65", ["poco c65", "pococ65"]),
    ("Xiaomi", "Xiaomi 11", "xiaomi-11", ["mi 11", "xiaomi 11"]),
    ("Xiaomi", "Xiaomi 11T", "xiaomi-11t", ["mi 11t", "xiaomi 11t"]),
    ("Xiaomi", "Xiaomi 12", "xiaomi-12", ["mi 12", "xiaomi 12"]),
    ("Xiaomi", "Xiaomi 12X", "xiaomi-12x", ["mi 12x", "xiaomi 12x"]),
    ("Xiaomi", "Xiaomi 13", "xiaomi-13", ["mi 13", "xiaomi 13"]),
    ("Xiaomi", "Xiaomi 13T", "xiaomi-13t", ["mi 13t", "xiaomi 13t"]),
    ("Xiaomi", "Xiaomi 14", "xiaomi-14", ["mi 14", "xiaomi 14"]),
    ("Xiaomi", "Xiaomi 14T", "xiaomi-14t", ["mi 14t", "xiaomi 14t"]),
    ("Honor", "X5", "honor-x5", ["honor x5", "x5"]),
    ("Honor", "X6", "honor-x6", ["honor x6", "x6"]),
    ("Honor", "X6A", "honor-x6a", ["honor x6a", "x6a"]),
    ("Honor", "X7", "honor-x7", ["honor x7", "x7"]),
    ("Honor", "X7A", "honor-x7a", ["honor x7a", "x7a"]),
    ("Honor", "X8A", "honor-x8a", ["honor x8a", "x8a"]),
    ("Honor", "X9", "honor-x9", ["honor x9", "x9"]),
    ("Honor", "X9A", "honor-x9a", ["honor x9a", "x9a"]),
    ("Honor", "X9B", "honor-x9b", ["honor x9b", "x9b"]),
    ("Honor", "X9C", "honor-x9c", ["honor x9c", "x9c"]),
    ("Honor", "70", "honor-70", ["70", "honor 70"]),
    ("Honor", "90", "honor-90", ["90", "honor 90"]),
    ("Honor", "Magic 5", "honor-magic-5", ["honor magic 5", "magic 5"]),
    ("Honor", "Magic 6", "honor-magic-6", ["honor magic 6", "magic 6"]),
    ("Huawei", "Y5", "huawei-y5", ["huawei y5", "y5"]),
    ("Huawei", "Y5 2018", "huawei-y52018", ["huawei y5 2018", "y5 2018"]),
    ("Huawei", "Y6", "huawei-y6", ["huawei y6", "y6"]),
    ("Huawei", "Y6 2019", "huawei-y62019", ["huawei y6 2019", "y6 2019"]),
    ("Huawei", "Y7", "huawei-y7", ["huawei y7", "y7"]),
    ("Huawei", "Y8", "huawei-y8", ["huawei y8", "y8"]),
    ("Huawei", "Y9", "huawei-y9", ["huawei y9", "y9"]),
    ("Huawei", "Y9 2018", "huawei-y92018", ["huawei y9 2018", "y9 2018"]),
    ("Huawei", "Nova 2", "huawei-nova2", ["huawei nova 2", "nova 2"]),
    ("Huawei", "Nova 3", "huawei-nova3", ["huawei nova 3", "nova 3"]),
    ("Huawei", "Nova 10", "huawei-nova10", ["huawei nova 10", "nova 10"]),
    ("Huawei", "P50", "huawei-p50", ["huawei p50", "p50"]),
    ("Realme", "Realme C30", "realme-c30", ["realme c30", "realmec30"]),
    ("Realme", "Realme C35", "realme-c35", ["realme c35", "realmec35"]),
    ("Realme", "Realme C51", "realme-c51", ["realme c51", "realmec51"]),
    ("Realme", "Realme C55", "realme-c55", ["realme c55", "realmec55"]),
    ("Realme", "Realme 9", "realme-9", ["realme 9", "realme9"]),
    ("Realme", "Realme 10", "realme-10", ["realme 10", "realme10"]),
    ("Realme", "Realme 11", "realme-11", ["realme 11", "realme11"]),
    ("Realme", "Realme 12", "realme-12", ["realme 12", "realme12"]),
    ("Realme", "Realme 13", "realme-13", ["realme 13", "realme13"]),
    ("Realme", "Realme 14", "realme-14", ["realme 14", "realme14"]),
    ("Realme", "Realme 15", "realme-15", ["realme 15", "realme15"]),
    ("Tecno", "Camon 19", "tecno-camon-19", ["camon 19", "tecno camon 19"]),
    ("Tecno", "Camon 20", "tecno-camon-20", ["camon 20", "tecno camon 20"]),
    ("Tecno", "Camon 30", "tecno-camon-30", ["camon 30", "tecno camon 30"]),
    ("Tecno", "Camon 40", "tecno-camon-40", ["camon 40", "tecno camon 40"]),
    ("Tecno", "Spark 20", "tecno-spark-20", ["spark 20", "tecno spark 20"]),
    ("Tecno", "Pop 7", "tecno-pop-7", ["pop 7", "tecno pop 7"]),
    ("Tecno", "Pop 8", "tecno-pop-8", ["pop 8", "tecno pop 8"]),
    ("Infinix", "Hot 12", "infinix-hot-12", ["hot 12", "infinix hot 12"]),
    ("Infinix", "Hot 20", "infinix-hot-20", ["hot 20", "infinix hot 20"]),
    ("Infinix", "Hot 30", "infinix-hot-30", ["hot 30", "infinix hot 30"]),
    ("Infinix", "Hot 30i", "infinix-hot-30i", ["hot 30i", "infinix hot 30i"]),
    ("Infinix", "Hot 40", "infinix-hot-40", ["hot 40", "infinix hot 40"]),
    ("Infinix", "Smart 7", "infinix-smart-7", ["infinix smart 7", "smart 7"]),
    (
        "Infinix",
        "Smart 7 Plus",
        "infinix-smart-7-plus",
        ["infinix smart 7 plus", "smart 7 plus", "infinix smart 7plus", "smart 7plus"],
    ),
    ("Infinix", "Smart 8", "infinix-smart-8", ["infinix smart 8", "smart 8"]),
    ("Infinix", "Note 30", "infinix-note-30", ["infinix note 30", "note 30"]),
    ("Tecno", "Spark 40", "tecno-spark-40", ["tecno spark 40", "spark 40"]),
    ("Tecno", "Spark Go", "tecno-spark-go", ["tecno spark go", "spark go"]),
    ("Tecno", "Pop 4", "tecno-pop-4", ["tecno pop 4", "pop 4"]),
    ("Infinix", "Hot 60", "infinix-hot-60", ["infinix hot 60", "hot 60", "hot 60i"]),
    ("Infinix", "Note 50", "infinix-note-50", ["infinix note 50", "note 50"]),
    ("Xiaomi", "Redmi A3", "xiaomi-redmi-a3", ["redmi a3", "a3x", "redmi a3x"]),
    ("Realme", "Realme C63", "realme-c63", ["realme c63", "c63"]),
    ("Huawei", "Nova Y73", "huawei-nova-y73", ["nova y73", "y73"]),
    ("Huawei", "Nova 13", "huawei-nova-13", ["nova 13", "nova13"]),
    ("Huawei", "Y8S", "huawei-y8s", ["y8s", "huawei y8s"]),
    ("Tecno", "Spark 8 Pro", "tecno-spark-8-pro", ["tecno spark 8 pro", "spark 8 pro"]),
    ("Tecno", "Spark 10 Pro", "tecno-spark-10-pro", ["tecno spark 10 pro", "spark 10 pro"]),
    ("Tecno", "Spark 40 Pro", "tecno-spark-40-pro", ["tecno spark 40 pro", "spark 40 pro"]),
    ("Tecno", "Pop 4 Pro", "tecno-pop-4-pro", ["tecno pop 4 pro", "pop 4 pro"]),
    ("Tecno", "Camon 30 Pro", "tecno-camon-30-pro", ["tecno camon 30 pro", "camon 30 pro"]),
    ("Tecno", "Pova 6", "tecno-pova-6", ["tecno pova 6", "pova 6"]),
    ("Tecno", "Pova 6 Pro", "tecno-pova-6-pro", ["tecno pova 6 pro", "pova 6 pro"]),
    ("Infinix", "Note 11 Pro", "infinix-note-11-pro", ["infinix note 11 pro", "note11pro"]),
    ("Infinix", "Note 12 Pro", "infinix-note-12-pro", ["infinix note 12 pro", "note12pro"]),
    ("Infinix", "Note 30 Pro", "infinix-note-30-pro", ["infinix note 30 pro", "note 30 pro"]),
    ("Infinix", "Note 50 Pro", "infinix-note-50-pro", ["infinix note 50 pro", "note 50 pro"]),
    ("Infinix", "Hot 40i", "infinix-hot-40i", ["infinix hot 40i", "hot 40i"]),
    ("Huawei", "Nova 13 Pro", "huawei-nova-13-pro", ["huawei nova 13 pro", "nova 13 pro"]),
    ("Xiaomi", "POCO M7 Pro", "xiaomi-poco-m7-pro", ["poco m7 pro", "m7 pro"]),
    ("Xiaomi", "POCO F6 Pro", "xiaomi-poco-f6-pro", ["poco f6 pro", "f6 pro"]),
    ("Xiaomi", "POCO F3 Pro", "xiaomi-poco-f3-pro", ["poco f3 pro", "f3 pro"]),
    ("Xiaomi", "Xiaomi 13T Pro", "xiaomi-13t-pro", ["xiaomi 13t pro", "13t pro"]),
    ("Xiaomi", "Xiaomi 14T Pro", "xiaomi-14t-pro", ["xiaomi 14t pro", "14t pro"]),
    (
        "Xiaomi",
        "Redmi Note 12 Pro Plus",
        "xiaomi-redmi-note-12-pro-plus",
        ["redmi note 12 pro plus", "note 12 pro+"],
    ),
    ("Honor", "Honor 8", "honor-8", ["honor 8", "хонор 8"]),
    ("Honor", "Honor 8 Lite", "honor-8-lite", ["honor 8 lite", "honor 8 pro"]),
    ("Honor", "Honor 8C", "honor-8c", ["honor 8c", "хонор 8c"]),
    ("Honor", "Honor 9", "honor-9", ["honor 9", "хонор 9"]),
    ("Honor", "Honor 9 Lite", "honor-9-lite", ["honor 9 lite", "honor honor 9 lite"]),
    ("Honor", "Honor 9A", "honor-9a", ["honor 9a", "хонор 9a"]),
    ("Honor", "Honor 10", "honor-10", ["honor 10", "хонор 10"]),
    ("Honor", "Honor 10X Lite", "honor-10x-lite", ["honor 10x lite", "honor honor 10x lite"]),
    ("Honor", "Honor 20", "honor-20", ["honor 20", "хонор 20"]),
    ("Honor", "Honor 20 Lite", "honor-20-lite", ["honor 20 lite", "honor honor 20 lite"]),
    ("Honor", "Honor 20 Pro", "honor-20-pro", ["honor 20 pro", "honor honor 20 pro"]),
    ("Honor", "Honor 30", "honor-30", ["honor 30", "хонор 30"]),
    ("Honor", "Honor 30i", "honor-30i", ["honor 30i", "honor honor 30i"]),
    ("Honor", "Honor 200", "honor-200", ["honor 200", "хонор 200"]),
    ("Honor", "Honor 200 Pro", "honor-200-pro", ["honor 200 pro", "honor honor 200 pro"]),
    ("Honor", "Honor 7X", "honor-7x", ["honor 7x", "хонор 7x"]),
    ("Xiaomi", "Redmi 4A", "xiaomi-redmi-4a", ["redmi 4a", "редми 4a"]),
    ("Xiaomi", "Redmi 4X", "xiaomi-redmi-4x", ["redmi 4x", "редми 4x"]),
    ("Xiaomi", "Redmi 5", "xiaomi-redmi-5", ["redmi 5", "редми 5"]),
    ("Xiaomi", "Redmi 5 Plus", "xiaomi-redmi-5-plus", ["redmi 5 plus", "редми 5 плюс"]),
    ("Xiaomi", "Redmi 7", "xiaomi-redmi-7", ["redmi 7", "редми 7"]),
    ("Xiaomi", "Redmi 7A", "xiaomi-redmi-7a", ["redmi 7a", "редми 7a"]),
    ("Xiaomi", "Redmi Note 4X", "xiaomi-redmi-note-4x", ["redmi note 4x", "редми ноут 4x"]),
    ("Xiaomi", "Redmi Note 5A", "xiaomi-redmi-note-5a", ["redmi note 5a", "xiaomi redmi note 5a"]),
    (
        "Xiaomi",
        "Redmi Note 10S",
        "xiaomi-redmi-note-10s",
        ["redmi note 10s", "xiaomi redmi note 10s"],
    ),
    (
        "Xiaomi",
        "Redmi Note 12S",
        "xiaomi-redmi-note-12s",
        ["redmi note 12s", "xiaomi redmi note 12s"],
    ),
    ("Xiaomi", "Redmi A1", "xiaomi-redmi-a1", ["redmi a1", "редми a1"]),
    ("Xiaomi", "Redmi A2", "xiaomi-redmi-a2", ["redmi a2", "редми a2"]),
    ("Realme", "Realme 6S", "realme-6s", ["realme 6s", "рилми 6s"]),
    ("Realme", "Realme 8i", "realme-8i", ["realme 8i", "рилми 8i"]),
    ("Realme", "Realme C2", "realme-c2", ["realme c2", "рилми c2"]),
    ("Realme", "Realme C3", "realme-c3", ["realme c3", "рилми c3"]),
    ("Realme", "Realme C25Y", "realme-c25y", ["realme c25y", "realme realme c25y"]),
    ("Realme", "Realme C31", "realme-c31", ["realme c31", "realme realme c31"]),
    ("Realme", "Realme C65", "realme-c65", ["realme c65", "c65"]),
    ("OPPO", "OPPO A1k", "oppo-a1k", ["oppo a1k", "оппо a1k"]),
    ("OPPO", "OPPO A5", "oppo-a5", ["oppo a5", "оппо a5"]),
    ("OPPO", "OPPO A17", "oppo-a17", ["oppo a17", "оппо a17"]),
    ("OPPO", "OPPO A53", "oppo-a53", ["oppo a53", "оппо a53"]),
    ("OPPO", "OPPO A74", "oppo-a74", ["oppo a74", "оппо a74"]),
    ("OPPO", "OPPO Reno 2F", "oppo-reno-2f", ["oppo reno 2f", "reno 2f"]),
    ("Samsung", "Galaxy A05s", "samsung-galaxy-a05s", ["a057f", "a05s"]),
    ("Samsung", "Galaxy A20s", "samsung-galaxy-a20s", ["a207f", "a20s"]),
    ("Tecno", "Tecno Spark 8C", "tecno-spark-8c", ["tecno spark 8c", "spark 8c"]),
    (
        "Infinix",
        "Infinix GT 10 Pro",
        "infinix-gt-10-pro",
        ["infinix gt 10 pro", "infinix infinix gt 10 pro"],
    ),
    (
        "Infinix",
        "Infinix GT 20 Pro",
        "infinix-gt-20-pro",
        ["infinix gt 20 pro", "infinix infinix gt 20 pro"],
    ),
    ("Infinix", "Infinix GT 30", "infinix-gt-30", ["infinix gt 30", "infinix infinix gt 30"]),
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
