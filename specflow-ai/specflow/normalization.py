"""
Детерминированная нормализация инженерных данных.

Модуль не зависит от LLM и используется всеми этапами пайплайна:
  * позиционные обозначения (ГОСТ 2.710 / IEC 81346): нормализация, раскрытие
    диапазонов «QF1-QF6», «XT1:1…24», «KM1.1÷KM1.4»;
  * числа в «инженерной» записи: «4,5», «16А», «~230 В», «0.03»;
  * единицы измерения (кириллица/латиница) и приведение к базовым единицам;
  * полюсность «3P+N», «1П+Н», кривые отключения «C16» и т.п.

Все функции чистые (без побочных эффектов) и покрыты тестами.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

# ---------------------------------------------------------------------------
# Позиционные обозначения
# ---------------------------------------------------------------------------

# Кириллические буквы, визуально совпадающие с латинскими. На российских
# чертежах «КМ1», «ХТ1», «НL1» часто набраны кириллицей, а в таблице
# спецификации — латиницей. Без приведения дубли между листами не найти.
_CYR_TO_LAT = str.maketrans(
    {
        "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H",
        "О": "O", "Р": "P", "С": "C", "Т": "T", "Х": "X", "У": "Y",
        "а": "A", "в": "B", "е": "E", "к": "K", "м": "M", "н": "H",
        "о": "O", "р": "P", "с": "C", "т": "T", "х": "X", "у": "Y",
    }
)

# Разделители диапазонов: «…», «⋯», «‥», «...», «..», «÷», тире, дефис.
# «⋯» (U+22EF) и «‥» (U+2025) встречаются в PDF из САПР, где шрифт подменяет
# многоточие похожим глифом, — без них «QF1⋯QF6» не раскрылся бы.
_RANGE_SEP_RE = re.compile(r"\s*(?:\.{2,3}|…|⋯|‥|÷|–|—|-)\s*")
_LIST_SEP_RE = re.compile(r"[,;\n]+")
_TRAILING_NUM_RE = re.compile(r"^(?P<prefix>.*?)(?P<num>\d+)$")
# Префиксы IEC 81346: функциональный аспект «=», аспект места «+».
_IEC_PREFIX_RE = re.compile(r"^(?:[=+][A-Z0-9.]+)+(?=-|$)")

MAX_RANGE_EXPANSION = 1000


def normalize_designation(raw: str) -> str:
    """Приводит позиционное обозначение к канонической форме.

    >>> normalize_designation(" -км1 ")
    'KM1'
    >>> normalize_designation("=A1+B2-QF1")
    'QF1'
    """
    if not raw:
        return ""
    s = unicodedata.normalize("NFKC", raw).strip().translate(_CYR_TO_LAT).upper()
    s = re.sub(r"\s+", "", s)
    s = _IEC_PREFIX_RE.sub("", s)
    s = s.lstrip("-")
    return s


def _expand_single(token: str) -> list[str]:
    """Раскрывает один элемент списка: «QF1-QF6» -> [QF1..QF6]."""
    token = normalize_designation(token)
    if not token:
        return []

    parts = [p for p in _RANGE_SEP_RE.split(token) if p]
    if len(parts) != 2:
        return [token]

    left, right = parts
    m_left = _TRAILING_NUM_RE.match(left)
    if not m_left:
        return [token]

    prefix = m_left.group("prefix")
    start = int(m_left.group("num"))

    if right.isdigit():
        end = int(right)
    else:
        m_right = _TRAILING_NUM_RE.match(right)
        if not m_right or m_right.group("prefix") != prefix:
            # «QF1-KM3» — это не диапазон, а две разные позиции.
            return [left, right]
        end = int(m_right.group("num"))

    if not prefix or end < start or (end - start) >= MAX_RANGE_EXPANSION:
        return [token]

    width = len(m_left.group("num"))
    zero_padded = m_left.group("num").startswith("0") and width > 1
    return [f"{prefix}{str(n).zfill(width) if zero_padded else n}" for n in range(start, end + 1)]


def expand_designations(raw: str | None) -> list[str]:
    """Раскрывает запись позиционных обозначений в список уникальных тегов.

    Поддерживает списки через запятую/точку с запятой и диапазоны:

    >>> expand_designations("QF1-QF3, QF5")
    ['QF1', 'QF2', 'QF3', 'QF5']
    >>> expand_designations("XT1:1…4")
    ['XT1:1', 'XT1:2', 'XT1:3', 'XT1:4']
    """
    if not raw:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for chunk in _LIST_SEP_RE.split(raw):
        for tag in _expand_single(chunk):
            if tag and tag not in seen:
                seen.add(tag)
                result.append(tag)
    return result


def designation_letter_code(tag: str) -> str:
    """Буквенный код позиционного обозначения: «QF12» -> «QF», «XT1:5» -> «XT»."""
    m = re.match(r"^([A-Z]+)", normalize_designation(tag))
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Числа и единицы измерения
# ---------------------------------------------------------------------------

_NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?")
_RANGE_RE = re.compile(
    r"(?P<a>\d+(?:[.,]\d+)?)\s*(?:\.{2,3}|…|⋯|‥|÷|–|—|-|to|до)\s*(?P<b>\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)


def parse_number(value: str | float | int | None) -> float | None:
    """Извлекает первое число из строки: «4,5 кА» -> 4.5, «~230В» -> 230.0."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = unicodedata.normalize("NFKC", str(value)).replace(" ", " ").strip()
    if not text:
        return None
    # Пробелы-разделители тысяч: «1 250» -> «1250».
    text = re.sub(r"(?<=\d)\s(?=\d{3}\b)", "", text)
    m = _NUMBER_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", "."))
    except ValueError:
        return None


def parse_range(value: str | None) -> tuple[float, float] | None:
    """Разбирает диапазон «6-10», «0,63…1 А», «4 до 20» -> (min, max)."""
    if not value:
        return None
    text = unicodedata.normalize("NFKC", str(value))
    m = _RANGE_RE.search(text)
    if not m:
        return None
    a = float(m.group("a").replace(",", "."))
    b = float(m.group("b").replace(",", "."))
    return (min(a, b), max(a, b))


def parse_int(value: str | float | int | None) -> int | None:
    num = parse_number(value)
    if num is None:
        return None
    return int(round(num))


# Канонические токены единиц. Ключ — нормализованная запись (нижний регистр,
# без пробелов и точек), значение — канонический токен.
_UNIT_ALIASES: dict[str, str] = {
    # ток
    "a": "A", "а": "A", "amp": "A", "ампер": "A",
    "ma": "mA", "ма": "mA",
    "ka": "kA", "ка": "kA",
    # напряжение
    "v": "V", "в": "V", "vac": "V", "vdc": "V", "вac": "V", "вdc": "V",
    "kv": "kV", "кв": "kV",
    "mv": "mV", "мв": "mV",
    # мощность
    "w": "W", "вт": "W",
    "kw": "kW", "квт": "kW",
    "mw": "MW", "мвт": "MW",
    "va": "VA", "ва": "VA",
    "kva": "kVA", "ква": "kVA",
    # частота
    "hz": "Hz", "гц": "Hz",
    # длина
    "mm": "mm", "мм": "mm",
    "cm": "cm", "см": "cm",
    "m": "m", "м": "m",
    "km": "km", "км": "km",
    # сечение
    "mm2": "mm2", "мм2": "mm2", "mm²": "mm2", "мм²": "mm2", "квмм": "mm2",
    "sqmm": "mm2",
    # прочее
    "%": "%",
    "°c": "C", "°с": "C",
    "bar": "bar", "бар": "bar",
    "mpa": "MPa", "мпа": "MPa",
    "kpa": "kPa", "кпа": "kPa",
    "pa": "Pa", "па": "Pa",
}

# Множители к базовой единице физической величины.
_UNIT_FACTORS: dict[str, tuple[str, float]] = {
    "A": ("A", 1.0), "mA": ("A", 1e-3), "kA": ("A", 1e3),
    "V": ("V", 1.0), "kV": ("V", 1e3), "mV": ("V", 1e-3),
    "W": ("W", 1.0), "kW": ("W", 1e3), "MW": ("W", 1e6),
    "VA": ("VA", 1.0), "kVA": ("VA", 1e3),
    "Hz": ("Hz", 1.0),
    "mm": ("m", 1e-3), "cm": ("m", 1e-2), "m": ("m", 1.0), "km": ("m", 1e3),
    "mm2": ("mm2", 1.0),
    "Pa": ("Pa", 1.0), "kPa": ("Pa", 1e3), "MPa": ("Pa", 1e6), "bar": ("Pa", 1e5),
}


def normalize_unit(unit: str | None) -> str:
    """Приводит запись единицы к каноническому токену: «кА» -> «kA», «мм²» -> «mm2».

    Неизвестные единицы возвращаются как есть (обрезанные).
    """
    if not unit:
        return ""
    raw = unicodedata.normalize("NFKC", unit).strip()
    key = re.sub(r"[\s.]", "", raw).lower().replace("²", "2")
    if key in _UNIT_ALIASES:
        return _UNIT_ALIASES[key]
    # «АС», «~», «DC» и т.п. — тип тока, а не единица.
    return raw


def split_value_unit(text: str | None) -> tuple[float | None, str]:
    """«16 А» -> (16.0, 'A'); «4,5кА» -> (4.5, 'kA'); «C16» -> (16.0, '')."""
    if not text:
        return None, ""
    s = unicodedata.normalize("NFKC", str(text)).strip()
    m = _NUMBER_RE.search(s)
    if not m:
        return None, ""
    number = float(m.group(0).replace(",", "."))
    tail = s[m.end():].strip()
    unit_match = re.match(r"^([A-Za-zА-Яа-я°%²2]+)", tail)
    unit = normalize_unit(unit_match.group(1)) if unit_match else ""
    if unit not in _UNIT_FACTORS and unit != "%" and unit != "C":
        unit = ""
    return number, unit


def is_convertible_unit(unit: str | None) -> bool:
    return normalize_unit(unit) in _UNIT_FACTORS


_ALL_NUMBERS_RE = re.compile(r"\d+(?:[.,]\d+)?")
_TRAILING_UNIT_RE = re.compile(r"\d\s*([A-Za-zА-Яа-я°%²]+)[^\d]*$")


def value_in_unit(
    value: str | None,
    unit: str | None,
    target: str,
    *,
    prefer_max: bool = False,
) -> float | None:
    """Значение параметра в целевой единице с учётом единицы внутри строки.

    * единица в самой строке («0,4 кВ», «24VDC») приоритетнее отдельной;
    * ``prefer_max`` — для записей с двумя номиналами «230/400 В» берётся больший;
    * без единицы число считается уже выраженным в целевой единице.

    >>> value_in_unit("0,4 кВ", "", "V")
    400.0
    >>> value_in_unit("230/400", "В", "V", prefer_max=True)
    400.0
    """
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", str(value)).strip()
    nums = [float(n.replace(",", ".")) for n in _ALL_NUMBERS_RE.findall(text)]
    if not nums:
        return None
    number = max(nums) if prefer_max and "/" in text else nums[0]
    m = _TRAILING_UNIT_RE.search(text)
    inline = normalize_unit(m.group(1)) if m else ""
    src = inline if inline in _UNIT_FACTORS else normalize_unit(unit)
    if src not in _UNIT_FACTORS:
        return number
    converted = convert_unit(number, src, target)
    return number if converted is None else converted


def convert_unit(value: float, from_unit: str, to_unit: str) -> float | None:
    """Пересчёт между единицами одной величины. None — если величины разные."""
    src = _UNIT_FACTORS.get(normalize_unit(from_unit))
    dst = _UNIT_FACTORS.get(normalize_unit(to_unit))
    if not src or not dst or src[0] != dst[0]:
        return None
    return value * src[1] / dst[1]


def to_unit(value: str | float | None, unit: str | None, target: str) -> float | None:
    """Разбирает значение с единицей и приводит к целевой.

    Если единица не указана ни в значении, ни отдельно — число считается уже
    выраженным в целевой единице (так обычно и пишут в таблицах: «Iн, А | 16»).

    >>> to_unit("0,03", "А", "mA")
    30.0
    >>> to_unit("4.5", "кА", "kA")
    4.5
    """
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number, inline_unit = float(value), ""
    else:
        number, inline_unit = split_value_unit(str(value))
    if number is None:
        return None
    src_unit = inline_unit or normalize_unit(unit)
    if not src_unit or src_unit not in _UNIT_FACTORS:
        return number
    converted = convert_unit(number, src_unit, target)
    return number if converted is None else converted


# ---------------------------------------------------------------------------
# Специфические параметры электрооборудования
# ---------------------------------------------------------------------------

_POLES_STRICT_RE = re.compile(
    r"(?<![\d.,])(?P<n>[1-4])\s*(?:P|П|POLE|-?ПОЛ\w*)(?P<neutral>\s*\+\s*(?:N|Н))?",
    re.IGNORECASE,
)
_POLES_BARE_RE = re.compile(r"^\s*(?P<n>[1-4])\s*(?P<neutral>\+\s*(?:N|Н))?\s*$", re.IGNORECASE)


def parse_poles(value: str | int | None) -> tuple[int | None, bool]:
    """«3P+N» -> (3, True); «1П+Н» -> (1, True); «4P» -> (4, False); 2 -> (2, False).

    Число без маркера полюсов распознаётся только если строка состоит из него
    целиком — иначе «16A 3P» дало бы «1 полюс».
    """
    if value is None or isinstance(value, bool):
        return None, False
    if isinstance(value, int):
        return (value, False) if 1 <= value <= 4 else (None, False)
    s = unicodedata.normalize("NFKC", str(value)).strip()
    m = _POLES_STRICT_RE.search(s) or _POLES_BARE_RE.match(s)
    if not m:
        return None, False
    return int(m.group("n")), bool(m.group("neutral"))


_TRIP_CURVE_RE = re.compile(r"(?<![A-Za-zА-Яа-я])([BCDKZbcdkzВСДКвсдк])(?:\s*\d|$|\s|-)")
_CURVE_CYR = {"В": "B", "С": "C", "Д": "D", "К": "K"}


def parse_trip_curve(value: str | None) -> str | None:
    """Кривая (характеристика) отключения: «C16» -> «C», «хар-ка D» -> «D»."""
    if not value:
        return None
    s = unicodedata.normalize("NFKC", str(value)).strip()
    if len(s) == 1:
        letter = _CURVE_CYR.get(s.upper(), s.upper())
        return letter if letter in {"B", "C", "D", "K", "Z"} else None
    for m in _TRIP_CURVE_RE.finditer(s + " "):
        letter = m.group(1).upper()
        letter = _CURVE_CYR.get(letter, letter)
        if letter in {"B", "C", "D", "K", "Z"}:
            return letter
    return None


def parse_dimensions_mm(value: str | None) -> tuple[float | None, float | None, float | None]:
    """«85x90x70», «85×90×70 мм», «600*800*250» -> (W, H, D) в мм."""
    if not value:
        return None, None, None
    s = unicodedata.normalize("NFKC", str(value))
    nums = [float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", s)]
    if not nums:
        return None, None, None
    nums = (nums + [None, None, None])[:3]  # type: ignore[list-item]
    return nums[0], nums[1], nums[2]


def parse_contacts(value: str | None) -> tuple[int, int]:
    """Конфигурация контактов: «1NO+1NC», «2З+1Р», «1НО» -> (NO, NC)."""
    if not value:
        return 0, 0
    s = unicodedata.normalize("NFKC", str(value)).upper().replace(" ", "")
    no = 0
    nc = 0
    for count, kind in re.findall(r"(\d*)(NO|NC|НО|НЗ|З|Р|CO|П)", s):
        n = int(count) if count else 1
        if kind in {"NO", "НО", "З"}:
            no += n
        elif kind in {"NC", "НЗ", "Р"}:
            nc += n
        elif kind in {"CO", "П"}:  # перекидной = 1NO + 1NC
            no += n
            nc += n
    return no, nc


def clamp01(value: float | int | None, default: float = 0.0) -> float:
    """Ограничивает число отрезком [0, 1]; проценты (1..100) переводит в доли."""
    if value is None:
        return default
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    if 1.0 < v <= 100.0:
        v = v / 100.0
    return max(0.0, min(1.0, v))


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out
