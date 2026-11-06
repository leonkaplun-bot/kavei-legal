"""
SpecFlow AI — Pydantic v2 схемы данных всего пайплайна.

Структура модуля
================
1. Базовые классы и утилиты (деньги, идентификаторы, время).
2. Справочники (Enum) с русскими подписями для UI и Excel.
3. Этап 0 — обработка PDF: страницы, тайлы, текстовый слой, таблицы.
4. Технические параметры: «сырой» параметр от LLM и типизированные ТХ.
5. Агент 1 (Vision Extractor): контракт ответа LLM + ExtractedRawBOM.
6. Агент 2 (Engineering Validator): контракт ответа LLM + ValidatedEngineeringBOM.
7. Агент 3 (Catalog Matcher): позиция прайса, кандидаты, контракт LLM + PricedBOM.
8. Агент 4 (Estimator): настройки КП, строки сметы, итоги, результат экспорта.
9. Наблюдаемость: токены, стоимость вызовов, события для live-лога, прогон.

Два вида моделей
================
* ``LLMContract`` — то, что заполняет модель Claude (Structured Outputs / Tool Use).
  Правила: плоские типы, все поля обязательные, без ``dict``-полей, без
  рекурсии, минимум ``Optional``. «Нет данных» = пустая строка / пустой список.
  Описания полей (``description``) попадают в JSON Schema и работают как часть
  промпта, поэтому они написаны как инструкции инженеру.
* ``SpecFlowModel`` — внутренние доменные модели: Optional, Decimal для денег,
  вычисляемые поля, ссылки на источники. Их строит детерминированный код.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from specflow.normalization import (
    clamp01,
    expand_designations,
    normalize_designation,
    normalize_unit,
    parse_contacts,
    parse_dimensions_mm,
    parse_int,
    parse_number,
    parse_poles,
    parse_range,
    parse_trip_curve,
    to_unit,
    unique_preserve_order,
    value_in_unit,
)

SCHEMA_VERSION = "1.0.0"

# =============================================================================
# 1. Базовые классы и утилиты
# =============================================================================

MONEY_QUANT = Decimal("0.01")
RATE_QUANT = Decimal("0.000001")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uid(prefix: str) -> str:
    """Короткий читаемый идентификатор: «c_3f9a1b2c4d»."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def to_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    """Безопасное приведение к Decimal (float -> через str, чтобы не тащить шум)."""
    if value is None or value == "":
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return default
    try:
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return default
            return Decimal(repr(value))
        if isinstance(value, int):
            return Decimal(value)
        text = str(value).strip().replace(" ", "").replace(" ", "").replace(",", ".")
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return default


def money(value: Decimal) -> Decimal:
    """Округление денежной суммы до копеек/агорот по правилу ROUND_HALF_UP."""
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _empty_to_none(value: Any) -> Any:
    if isinstance(value, str) and not value.strip():
        return None
    return value


class SpecFlowModel(BaseModel):
    """База внутренних доменных моделей.

    Вычисляемые поля (``@computed_field``) попадают в JSON-артефакты этапов.
    При обратной загрузке они отбрасываются и пересчитываются — иначе
    ``extra="forbid"`` отклонил бы собственный сохранённый артефакт.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _drop_computed_fields(cls, data: Any) -> Any:
        computed = cls.model_computed_fields
        if computed and isinstance(data, dict):
            return {k: v for k, v in data.items() if k not in computed}
        return data


class LLMContract(BaseModel):
    """База моделей, которые заполняет Claude через Structured Outputs.

    ``extra="forbid"`` даёт ``additionalProperties: false`` в JSON Schema —
    обязательное требование strict-режима.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# =============================================================================
# 2. Справочники
# =============================================================================


class ComponentCategory(StrEnum):
    """Категория изделия. Значения — стабильные ключи (английский snake_case)."""

    CIRCUIT_BREAKER = "circuit_breaker"
    RCD = "rcd"
    RCBO = "rcbo"
    SWITCH_DISCONNECTOR = "switch_disconnector"
    CHANGEOVER_SWITCH = "changeover_switch"
    FUSE = "fuse"
    FUSE_HOLDER = "fuse_holder"
    MOTOR_PROTECTION_BREAKER = "motor_protection_breaker"
    CONTACTOR = "contactor"
    THERMAL_OVERLOAD_RELAY = "thermal_overload_relay"
    CONTROL_RELAY = "control_relay"
    TIME_RELAY = "time_relay"
    MONITORING_RELAY = "monitoring_relay"
    SURGE_PROTECTOR = "surge_protector"
    ATS_CONTROLLER = "ats_controller"
    PLC = "plc"
    PLC_MODULE = "plc_module"
    HMI = "hmi"
    POWER_SUPPLY = "power_supply"
    UPS = "ups"
    VFD = "vfd"
    SOFT_STARTER = "soft_starter"
    CONTROL_TRANSFORMER = "control_transformer"
    CURRENT_TRANSFORMER = "current_transformer"
    ENERGY_METER = "energy_meter"
    MEASURING_INSTRUMENT = "measuring_instrument"
    PILOT_LIGHT = "pilot_light"
    PUSHBUTTON = "pushbutton"
    SELECTOR_SWITCH = "selector_switch"
    EMERGENCY_STOP = "emergency_stop"
    SENSOR = "sensor"
    TRANSMITTER = "transmitter"
    ACTUATOR = "actuator"
    MOTOR = "motor"
    HEATER = "heater"
    ENCLOSURE_CLIMATE = "enclosure_climate"
    NETWORK_DEVICE = "network_device"
    ENCLOSURE = "enclosure"
    ENCLOSURE_ACCESSORY = "enclosure_accessory"
    TERMINAL_BLOCK = "terminal_block"
    TERMINAL_ACCESSORY = "terminal_accessory"
    DIN_RAIL = "din_rail"
    CABLE_DUCT = "cable_duct"
    CABLE_GLAND = "cable_gland"
    WIRE_FERRULE = "wire_ferrule"
    MARKING = "marking"
    BUSBAR = "busbar"
    CABLE = "cable"
    WIRE = "wire"
    SOCKET = "socket"
    LIGHTING = "lighting"
    OTHER = "other"

    @property
    def label_ru(self) -> str:
        return CATEGORY_LABELS_RU[self]


CATEGORY_LABELS_RU: dict[ComponentCategory, str] = {
    ComponentCategory.CIRCUIT_BREAKER: "Автоматический выключатель",
    ComponentCategory.RCD: "УЗО (выключатель дифференциального тока)",
    ComponentCategory.RCBO: "Дифференциальный автомат (АВДТ)",
    ComponentCategory.SWITCH_DISCONNECTOR: "Выключатель нагрузки / рубильник",
    ComponentCategory.CHANGEOVER_SWITCH: "Переключатель ввода (1-0-2)",
    ComponentCategory.FUSE: "Плавкая вставка",
    ComponentCategory.FUSE_HOLDER: "Держатель предохранителя / предохранитель-разъединитель",
    ComponentCategory.MOTOR_PROTECTION_BREAKER: "Автомат защиты двигателя",
    ComponentCategory.CONTACTOR: "Контактор / пускатель",
    ComponentCategory.THERMAL_OVERLOAD_RELAY: "Тепловое реле перегрузки",
    ComponentCategory.CONTROL_RELAY: "Промежуточное реле",
    ComponentCategory.TIME_RELAY: "Реле времени",
    ComponentCategory.MONITORING_RELAY: "Реле контроля (фаз, напряжения, уровня)",
    ComponentCategory.SURGE_PROTECTOR: "УЗИП / ОПН",
    ComponentCategory.ATS_CONTROLLER: "Контроллер / блок АВР",
    ComponentCategory.PLC: "Программируемый логический контроллер",
    ComponentCategory.PLC_MODULE: "Модуль ввода-вывода / коммуникационный модуль ПЛК",
    ComponentCategory.HMI: "Панель оператора (HMI)",
    ComponentCategory.POWER_SUPPLY: "Блок питания",
    ComponentCategory.UPS: "ИБП / буферный модуль",
    ComponentCategory.VFD: "Преобразователь частоты",
    ComponentCategory.SOFT_STARTER: "Устройство плавного пуска",
    ComponentCategory.CONTROL_TRANSFORMER: "Трансформатор цепей управления",
    ComponentCategory.CURRENT_TRANSFORMER: "Трансформатор тока",
    ComponentCategory.ENERGY_METER: "Счётчик электроэнергии",
    ComponentCategory.MEASURING_INSTRUMENT: "Измерительный прибор (A, V, мультиметр)",
    ComponentCategory.PILOT_LIGHT: "Сигнальная арматура (лампа)",
    ComponentCategory.PUSHBUTTON: "Кнопка управления",
    ComponentCategory.SELECTOR_SWITCH: "Переключатель / кулачковый переключатель",
    ComponentCategory.EMERGENCY_STOP: "Кнопка аварийного останова",
    ComponentCategory.SENSOR: "Датчик дискретный (концевой, индуктивный и т.п.)",
    ComponentCategory.TRANSMITTER: "Измерительный преобразователь КИП",
    ComponentCategory.ACTUATOR: "Исполнительный механизм / клапан",
    ComponentCategory.MOTOR: "Электродвигатель",
    ComponentCategory.HEATER: "Нагреватель (технологический)",
    ComponentCategory.ENCLOSURE_CLIMATE: "Климат шкафа (вентилятор, термостат, обогрев)",
    ComponentCategory.NETWORK_DEVICE: "Сетевое оборудование",
    ComponentCategory.ENCLOSURE: "Шкаф / корпус / щит",
    ComponentCategory.ENCLOSURE_ACCESSORY: "Аксессуары корпуса (панель, замок, петли)",
    ComponentCategory.TERMINAL_BLOCK: "Клеммы",
    ComponentCategory.TERMINAL_ACCESSORY: "Аксессуары клемм (заглушки, перемычки, стопоры)",
    ComponentCategory.DIN_RAIL: "DIN-рейка",
    ComponentCategory.CABLE_DUCT: "Перфорированный кабель-канал",
    ComponentCategory.CABLE_GLAND: "Кабельный ввод (сальник PG/MG)",
    ComponentCategory.WIRE_FERRULE: "Наконечники (НШВИ / НКИ)",
    ComponentCategory.MARKING: "Маркировка",
    ComponentCategory.BUSBAR: "Шины / гребенчатые шины / шинодержатели",
    ComponentCategory.CABLE: "Кабель",
    ComponentCategory.WIRE: "Провод монтажный",
    ComponentCategory.SOCKET: "Розетка",
    ComponentCategory.LIGHTING: "Освещение шкафа / светильник",
    ComponentCategory.OTHER: "Прочее",
}

# Категории, которые Агент 2 добавляет как монтажные аксессуары.
ACCESSORY_CATEGORIES: frozenset[ComponentCategory] = frozenset(
    {
        ComponentCategory.TERMINAL_BLOCK,
        ComponentCategory.TERMINAL_ACCESSORY,
        ComponentCategory.DIN_RAIL,
        ComponentCategory.CABLE_DUCT,
        ComponentCategory.CABLE_GLAND,
        ComponentCategory.WIRE_FERRULE,
        ComponentCategory.MARKING,
        ComponentCategory.BUSBAR,
        ComponentCategory.WIRE,
        ComponentCategory.ENCLOSURE_ACCESSORY,
    }
)


class UnitOfMeasure(StrEnum):
    PCS = "pcs"
    M = "m"
    SET = "set"
    PACK = "pack"
    KG = "kg"

    @property
    def label_ru(self) -> str:
        return {
            UnitOfMeasure.PCS: "шт.",
            UnitOfMeasure.M: "м",
            UnitOfMeasure.SET: "компл.",
            UnitOfMeasure.PACK: "уп.",
            UnitOfMeasure.KG: "кг",
        }[self]


class SourceKind(StrEnum):
    """Откуда на листе взята позиция."""

    SCHEMATIC = "schematic"
    SPEC_TABLE = "spec_table"
    LAYOUT = "layout"
    TEXT = "text"
    TITLE_BLOCK = "title_block"
    LEGEND = "legend"


class QuantityBasis(StrEnum):
    STATED = "stated"
    COUNTED = "counted"
    INFERRED = "inferred"


class Readability(StrEnum):
    CLEAR = "clear"
    PARTIAL = "partial"
    UNREADABLE = "unreadable"


class DrawingType(StrEnum):
    SINGLE_LINE_DIAGRAM = "single_line_diagram"
    SCHEMATIC_DIAGRAM = "schematic_diagram"
    CONNECTION_DIAGRAM = "connection_diagram"
    PANEL_LAYOUT = "panel_layout"
    CABLE_SCHEDULE = "cable_schedule"
    EQUIPMENT_SPECIFICATION = "equipment_specification"
    ELEMENT_LIST = "element_list"
    TECHNICAL_REQUIREMENTS = "technical_requirements"
    COVER_SHEET = "cover_sheet"
    OTHER = "other"

    @property
    def label_ru(self) -> str:
        return {
            DrawingType.SINGLE_LINE_DIAGRAM: "Однолинейная схема",
            DrawingType.SCHEMATIC_DIAGRAM: "Схема электрическая принципиальная",
            DrawingType.CONNECTION_DIAGRAM: "Схема подключений / соединений",
            DrawingType.PANEL_LAYOUT: "Чертёж общего вида / расположения",
            DrawingType.CABLE_SCHEDULE: "Кабельный журнал",
            DrawingType.EQUIPMENT_SPECIFICATION: "Спецификация оборудования",
            DrawingType.ELEMENT_LIST: "Перечень элементов",
            DrawingType.TECHNICAL_REQUIREMENTS: "Техническое задание / требования",
            DrawingType.COVER_SHEET: "Титульный лист / общие данные",
            DrawingType.OTHER: "Прочее",
        }[self]


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class IssueType(StrEnum):
    MISSING_PARAMETER = "missing_parameter"
    INCONSISTENT_PARAMETER = "inconsistent_parameter"
    DUPLICATE = "duplicate"
    QUANTITY_MISMATCH = "quantity_mismatch"
    UNREADABLE = "unreadable"
    NONSTANDARD_VALUE = "nonstandard_value"
    PROTECTION_COORDINATION = "protection_coordination"
    CABLE_PROTECTION_MISMATCH = "cable_protection_mismatch"
    UNKNOWN_OR_OBSOLETE_MODEL = "unknown_or_obsolete_model"
    OTHER = "other"


class ItemOrigin(StrEnum):
    EXTRACTED = "extracted"
    MERGED = "merged"
    ACCESSORY_RULE = "accessory_rule"
    ACCESSORY_AI = "accessory_ai"
    MANUAL = "manual"

    @property
    def label_ru(self) -> str:
        return {
            ItemOrigin.EXTRACTED: "С чертежа",
            ItemOrigin.MERGED: "Объединено (дубль)",
            ItemOrigin.ACCESSORY_RULE: "Аксессуар (правило)",
            ItemOrigin.ACCESSORY_AI: "Аксессуар (ИИ)",
            ItemOrigin.MANUAL: "Вручную",
        }[self]


class ReviewStatus(StrEnum):
    OK = "ok"
    CORRECTED = "corrected"
    NEEDS_REVIEW = "needs_review"


class DuplicateResolution(StrEnum):
    MERGE = "merge"
    KEEP_SEPARATE = "keep_separate"


class MatchType(StrEnum):
    EXACT_SKU = "exact_sku"
    EXACT_SPECS = "exact_specs"
    ANALOG = "analog"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"

    @property
    def label_ru(self) -> str:
        return {
            MatchType.EXACT_SKU: "Точный артикул",
            MatchType.EXACT_SPECS: "Совпадение по ТХ",
            MatchType.ANALOG: "Аналог",
            MatchType.PARTIAL: "Частичное соответствие",
            MatchType.NOT_FOUND: "Не найдено",
        }[self]


class RetrievalMethod(StrEnum):
    SKU_EXACT = "sku_exact"
    FUZZY = "fuzzy"
    VECTOR = "vector"
    SPEC_FILTER = "spec_filter"


class NormSource(StrEnum):
    DEFAULT_TABLE = "default_table"
    AI_ESTIMATE = "ai_estimate"
    MANUAL = "manual"


class PipelineStage(StrEnum):
    PDF_PROCESSING = "pdf_processing"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    MATCHING = "matching"
    ESTIMATION = "estimation"
    EXPORT = "export"

    @property
    def label_ru(self) -> str:
        return {
            PipelineStage.PDF_PROCESSING: "Обработка PDF",
            PipelineStage.EXTRACTION: "Агент 1 · Дешифровка чертежей",
            PipelineStage.VALIDATION: "Агент 2 · Инженерный нормоконтроль",
            PipelineStage.MATCHING: "Агент 3 · Подбор по прайсам",
            PipelineStage.ESTIMATION: "Агент 4 · Сметный расчёт",
            PipelineStage.EXPORT: "Экспорт Excel",
        }[self]


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EventLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class PageKindHint(StrEnum):
    """Эвристическая классификация страницы по содержимому (без LLM)."""

    DRAWING = "drawing"
    SPEC_TABLE = "spec_table"
    TEXT_DOCUMENT = "text_document"
    SCANNED = "scanned"
    MIXED = "mixed"
    BLANK = "blank"


class RenderColorspace(StrEnum):
    RGB = "rgb"
    GRAY = "gray"


# =============================================================================
# 3. Этап 0 — обработка PDF
# =============================================================================

PDF_PROCESSOR_VERSION = "1.0.0"


class BBox(SpecFlowModel):
    """Прямоугольник в координатах страницы PDF (пункты, 1 pt = 1/72 дюйма)."""

    x0: float
    y0: float
    x1: float
    y1: float

    @model_validator(mode="after")
    def _ordered(self) -> BBox:
        if self.x1 < self.x0 or self.y1 < self.y0:
            x0, x1 = sorted((self.x0, self.x1))
            y0, y1 = sorted((self.y0, self.y1))
            # validate_assignment=True: присваиваем через __dict__, чтобы
            # не уйти в рекурсию валидатора.
            self.__dict__.update(x0=x0, y0=y0, x1=x1, y1=y1)
        return self

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0)

    def contains_point(self, x: float, y: float) -> bool:
        return self.x0 <= x <= self.x1 and self.y0 <= y <= self.y1

    def intersection_area(self, other: BBox) -> float:
        w = min(self.x1, other.x1) - max(self.x0, other.x0)
        h = min(self.y1, other.y1) - max(self.y0, other.y0)
        return w * h if w > 0 and h > 0 else 0.0

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)

    @classmethod
    def from_seq(cls, seq: Any) -> BBox:
        x0, y0, x1, y1 = (float(v) for v in tuple(seq)[:4])
        return cls(x0=x0, y0=y0, x1=x1, y1=y1)


class ImageAsset(SpecFlowModel):
    """Отрендеренное изображение на диске."""

    path: Path
    media_type: Literal["image/png", "image/jpeg"]
    width_px: int = Field(ge=1)
    height_px: int = Field(ge=1)
    size_bytes: int = Field(ge=0)
    dpi: float = Field(gt=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estimated_tokens(self) -> int:
        """Оценка стоимости картинки во входных токенах Claude (≈ W·H / 750)."""
        return math.ceil(self.width_px * self.height_px / 750)

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()


class TextWord(SpecFlowModel):
    text: str
    bbox: BBox


class ImageTile(SpecFlowModel):
    """Фрагмент страницы в полном разрешении для детального анализа Vision."""

    tile_id: str
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    bbox_pt: BBox
    image: ImageAsset
    text_hint: str = Field(
        default="",
        description="Текст из текстового слоя PDF, попадающий в тайл (построчно).",
    )


class ExtractedTable(SpecFlowModel):
    """Таблица, найденная в векторном слое (спецификация, перечень элементов)."""

    table_id: str
    page_number: int = Field(ge=1)
    bbox_pt: BBox
    header: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    markdown: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def row_count(self) -> int:
        return len(self.rows)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def col_count(self) -> int:
        return max((len(r) for r in self.rows), default=len(self.header))


class PageContentMetrics(SpecFlowModel):
    char_count: int = 0
    word_count: int = 0
    vector_paths: int = 0
    text_ops: int = 0
    raster_images: int = 0
    raster_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    likely_scanned: bool = False
    likely_outlined_text: bool = Field(
        default=False,
        description="Текст нарисован векторами (SHX-шрифты AutoCAD): текстового слоя нет, "
        "но надписи видны на изображении.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def has_text_layer(self) -> bool:
        return self.char_count > 0


class PdfProcessingOptions(SpecFlowModel):
    """Параметры рендеринга. Значения по умолчанию подобраны под чертежи А4–А0."""

    render_dpi: int = Field(default=300, ge=72, le=600)
    tile_max_edge_px: int = Field(default=1568, ge=256, le=8000)
    tile_max_pixels: int = Field(default=1_150_000, ge=65_536)
    tile_overlap_px: int = Field(default=180, ge=0)
    overview_max_edge_px: int = Field(default=1568, ge=256, le=8000)
    overview_max_pixels: int = Field(default=1_150_000, ge=65_536)
    colorspace: RenderColorspace = RenderColorspace.RGB
    save_full_page: bool = True
    full_page_max_megapixels: float = Field(default=80.0, gt=0)
    extract_text: bool = True
    extract_words: bool = True
    extract_tables: bool = True
    table_max_vector_paths: int = Field(default=60_000, ge=0)
    max_image_bytes: int = Field(default=3_750_000, ge=100_000)
    jpeg_quality: int = Field(default=90, ge=40, le=100)
    max_pages: int = Field(default=60, ge=1)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tile_side_px(self) -> int:
        """Сторона квадратного тайла: не больше лимита по стороне и по площади."""
        return int(min(self.tile_max_edge_px, math.isqrt(self.tile_max_pixels)))

    @model_validator(mode="after")
    def _check_overlap(self) -> PdfProcessingOptions:
        if self.tile_overlap_px * 2 >= self.tile_side_px:
            raise ValueError(
                f"tile_overlap_px={self.tile_overlap_px} слишком велик для тайла "
                f"{self.tile_side_px}px (перекрытие должно быть меньше половины тайла)"
            )
        return self

    def fingerprint(self) -> str:
        """Хэш параметров — ключ кэша отрендеренных страниц."""
        payload = self.model_dump(mode="json")
        payload["_processor_version"] = PDF_PROCESSOR_VERSION
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:12]


class PdfDocumentInfo(SpecFlowModel):
    document_id: str = Field(description="Первые 16 символов SHA-256 файла.")
    file_name: str
    file_path: Path
    sha256: str
    size_bytes: int = Field(ge=0)
    page_count: int = Field(ge=0)
    pdf_format: str = ""
    title: str = ""
    author: str = ""
    creator: str = ""
    producer: str = ""
    is_encrypted: bool = False


class PageFailure(SpecFlowModel):
    document_id: str
    page_number: int = Field(ge=1)
    stage: PipelineStage
    error: str


class ProcessedPage(SpecFlowModel):
    document_id: str
    page_number: int = Field(ge=1, description="Номер страницы с 1.")
    width_pt: float = Field(gt=0)
    height_pt: float = Field(gt=0)
    original_rotation: int = 0
    paper_format: str = Field(default="", description="A4, A3, A1, A4x3 … либо «нестандартный».")
    render_dpi: int
    overview: ImageAsset
    full_page: ImageAsset | None = None
    tiles: list[ImageTile] = Field(default_factory=list)
    text: str = ""
    words: list[TextWord] = Field(default_factory=list)
    tables: list[ExtractedTable] = Field(default_factory=list)
    metrics: PageContentMetrics = Field(default_factory=PageContentMetrics)
    kind_hint: PageKindHint = PageKindHint.MIXED
    warnings: list[str] = Field(default_factory=list)
    processing_time_s: float = 0.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estimated_image_tokens(self) -> int:
        """Входные токены, если отправить обзор страницы и все тайлы."""
        return self.overview.estimated_tokens + sum(t.image.estimated_tokens for t in self.tiles)

    def words_in(self, bbox: BBox) -> list[TextWord]:
        """Слова, центр которых попадает в прямоугольник."""
        return [w for w in self.words if bbox.contains_point(*w.bbox.center)]

    def text_in(self, bbox: BBox) -> str:
        return " ".join(w.text for w in self.words_in(bbox))


class ProcessedDocument(SpecFlowModel):
    info: PdfDocumentInfo
    options: PdfProcessingOptions
    output_dir: Path
    pages: list[ProcessedPage] = Field(default_factory=list)
    failures: list[PageFailure] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estimated_image_tokens(self) -> int:
        return sum(p.estimated_image_tokens for p in self.pages)

    @property
    def processed_page_numbers(self) -> list[int]:
        return [p.page_number for p in self.pages]

    def page(self, page_number: int) -> ProcessedPage:
        for p in self.pages:
            if p.page_number == page_number:
                return p
        raise KeyError(f"Страница {page_number} не обработана")


# =============================================================================
# 4. Технические параметры
# =============================================================================


class SpecKey(StrEnum):
    """Нормализованный ключ технического параметра."""

    RATED_CURRENT = "rated_current"
    RATED_VOLTAGE = "rated_voltage"
    CURRENT_TYPE = "current_type"
    FREQUENCY = "frequency"
    POLES = "poles"
    TRIP_CURVE = "trip_curve"
    BREAKING_CAPACITY = "breaking_capacity"
    RESIDUAL_CURRENT = "residual_current"
    RCD_TYPE = "rcd_type"
    RATED_POWER = "rated_power"
    COIL_VOLTAGE = "coil_voltage"
    MAIN_CONTACTS = "main_contacts"
    AUX_CONTACTS = "aux_contacts"
    UTILIZATION_CATEGORY = "utilization_category"
    SETTING_RANGE = "setting_range"
    CROSS_SECTION = "cross_section"
    CORES = "cores"
    CABLE_TYPE = "cable_type"
    LENGTH = "length"
    IP_RATING = "ip_rating"
    WIDTH_MODULES = "width_modules"
    DIMENSIONS = "dimensions"
    MOUNTING = "mounting"
    DIGITAL_INPUTS = "digital_inputs"
    DIGITAL_OUTPUTS = "digital_outputs"
    ANALOG_INPUTS = "analog_inputs"
    ANALOG_OUTPUTS = "analog_outputs"
    COMMUNICATION = "communication"
    MEASURED_VARIABLE = "measured_variable"
    MEASUREMENT_RANGE = "measurement_range"
    OUTPUT_SIGNAL = "output_signal"
    PROCESS_CONNECTION = "process_connection"
    ACCURACY_CLASS = "accuracy_class"
    COLOR = "color"
    CONTACT_CONFIGURATION = "contact_configuration"
    LAMP_VOLTAGE = "lamp_voltage"
    MATERIAL = "material"
    OTHER = "other"


class TechnicalParameter(LLMContract):
    """Один технический параметр «как в документе» + нормализованный ключ."""

    key: SpecKey = Field(
        description=(
            "Нормализованный ключ параметра. rated_current — номинальный ток In; "
            "breaking_capacity — отключающая способность Icu/Icn; residual_current — "
            "ток утечки IΔn; setting_range — диапазон уставки (тепловое реле, автомат "
            "защиты двигателя); cross_section — сечение жилы или «NxS» для кабеля; "
            "width_modules — ширина в DIN-модулях (17,5/18 мм); main_contacts — силовые "
            "контакты (3NO); aux_contacts — блок-контакты (1NO+1NC); "
            "contact_configuration — контакты кнопок/переключателей; other — всё, "
            "что не подходит под остальные ключи."
        )
    )
    name: str = Field(
        description="Название параметра дословно как в документе (например «Iн», "
        "«Ном. ток», «Icu»). Пустая строка, если параметр понятен только из маркировки."
    )
    value: str = Field(
        description="Значение дословно, без перевода единиц: «16», «C», «3P+N», «4,5», "
        "«5x2,5», «1NO+1NC», «AC-3», «24 VDC», «4-20 мА»."
    )
    unit: str = Field(
        description="Единица измерения как в документе («А», «кА», «мА», «В», «кВт», "
        "«мм²», «м»). Пустая строка, если единица не указана или входит в value."
    )


def _fmt_num(value: float | None) -> str:
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


class TechnicalSpecs(SpecFlowModel):
    """Типизированные ТХ изделия в базовых единицах (А, кА, мА, В, кВт, мм², м, мм).

    Строится детерминированно из списка ``TechnicalParameter``. Используется
    Агентом 2 (проверки) и Агентом 3 (сравнение с прайсом).
    """

    rated_current_a: float | None = None
    rated_voltage_v: float | None = None
    current_type: Literal["AC", "DC", "AC/DC"] | None = None
    frequency_hz: float | None = None
    poles: int | None = Field(default=None, ge=1, le=4)
    has_neutral: bool = False
    trip_curve: Literal["B", "C", "D", "K", "Z"] | None = None
    breaking_capacity_ka: float | None = None
    residual_current_ma: float | None = None
    rcd_type: str | None = None
    rated_power_kw: float | None = None
    coil_voltage_v: float | None = None
    coil_current_type: Literal["AC", "DC", "AC/DC"] | None = None
    main_contacts: str | None = None
    aux_contacts_no: int | None = None
    aux_contacts_nc: int | None = None
    utilization_category: str | None = None
    setting_range_min_a: float | None = None
    setting_range_max_a: float | None = None
    cross_section_mm2: float | None = None
    cores_count: int | None = None
    cable_type: str | None = None
    length_m: float | None = None
    ip_rating: str | None = None
    width_modules: float | None = None
    width_mm: float | None = None
    height_mm: float | None = None
    depth_mm: float | None = None
    mounting: str | None = None
    digital_inputs: int | None = None
    digital_outputs: int | None = None
    analog_inputs: int | None = None
    analog_outputs: int | None = None
    communication: list[str] = Field(default_factory=list)
    measured_variable: str | None = None
    measurement_range: str | None = None
    output_signal: str | None = None
    process_connection: str | None = None
    accuracy_class: str | None = None
    color: str | None = None
    contact_no: int | None = None
    contact_nc: int | None = None
    lamp_voltage_v: float | None = None
    material: str | None = None
    other: list[TechnicalParameter] = Field(default_factory=list)

    # --- построение из параметров LLM ---------------------------------------

    @staticmethod
    def _detect_current_type(text: str) -> Literal["AC", "DC", "AC/DC"] | None:
        upper = text.upper()
        latin = upper.translate(_CYR_TO_LAT_UPPER)
        has_ac = "AC" in latin or "~" in upper or "ПЕРЕМ" in upper
        has_dc = (
            "DC" in latin
            or "ПОСТ" in upper
            or "⎓" in upper
            or re.match(r"^\s*=\s*\d", upper) is not None
        )
        if re.search(r"\bUC\b", latin) or "УНИВ" in upper or (has_ac and has_dc):
            return "AC/DC"
        if has_ac:
            return "AC"
        if has_dc:
            return "DC"
        return None

    @classmethod
    def from_parameters(cls, params: list[TechnicalParameter]) -> TechnicalSpecs:
        """Строит ТХ из параметров. Нераспознанное и невалидное уходит в ``other``."""
        data: dict[str, Any] = {}
        provenance: dict[str, TechnicalParameter] = {}
        communication: list[str] = []
        other: list[TechnicalParameter] = []

        def put(field_name: str, value: Any, param: TechnicalParameter) -> None:
            if value is None or value == "":
                return
            data[field_name] = value
            provenance[field_name] = param

        for p in params:
            value = (p.value or "").strip()
            unit = (p.unit or "").strip()
            combined = f"{value} {unit}".strip()
            key = p.key
            if not value:
                continue

            if key is SpecKey.RATED_CURRENT:
                put("rated_current_a", value_in_unit(value, unit, "A"), p)
            elif key is SpecKey.RATED_VOLTAGE:
                put("rated_voltage_v", value_in_unit(value, unit, "V", prefer_max=True), p)
                if "current_type" not in data:
                    put("current_type", cls._detect_current_type(combined), p)
            elif key is SpecKey.CURRENT_TYPE:
                put("current_type", cls._detect_current_type(combined), p)
            elif key is SpecKey.FREQUENCY:
                put("frequency_hz", parse_number(value), p)
            elif key is SpecKey.POLES:
                poles, neutral = parse_poles(combined)
                if poles is None:
                    other.append(p)
                else:
                    put("poles", poles, p)
                    put("has_neutral", neutral, p)
            elif key is SpecKey.TRIP_CURVE:
                curve = parse_trip_curve(value)
                if curve is None:
                    other.append(p)
                else:
                    put("trip_curve", curve, p)
            elif key is SpecKey.BREAKING_CAPACITY:
                ka = value_in_unit(value, unit, "kA")
                # «4500» без единицы — это амперы: 4,5 кА.
                if ka is not None and ka > 200 and not normalize_unit(unit):
                    ka = ka / 1000.0
                put("breaking_capacity_ka", ka, p)
            elif key is SpecKey.RESIDUAL_CURRENT:
                ma = value_in_unit(value, unit, "mA")
                # «0,03» без единицы — это амперы: 30 мА.
                if ma is not None and ma < 1.0 and not normalize_unit(unit):
                    ma = ma * 1000.0
                put("residual_current_ma", ma, p)
            elif key is SpecKey.RCD_TYPE:
                put("rcd_type", re.sub(r"(?i)\b(тип|type)\b", "", value).strip().upper(), p)
            elif key is SpecKey.RATED_POWER:
                put("rated_power_kw", value_in_unit(value, unit, "kW"), p)
            elif key is SpecKey.COIL_VOLTAGE:
                put("coil_voltage_v", value_in_unit(value, unit, "V", prefer_max=True), p)
                put("coil_current_type", cls._detect_current_type(combined), p)
            elif key is SpecKey.MAIN_CONTACTS:
                put("main_contacts", value.upper().replace(" ", ""), p)
            elif key is SpecKey.AUX_CONTACTS:
                no, nc = parse_contacts(value)
                put("aux_contacts_no", no, p)
                put("aux_contacts_nc", nc, p)
            elif key is SpecKey.UTILIZATION_CATEGORY:
                put("utilization_category", value.upper().replace(" ", ""), p)
            elif key is SpecKey.SETTING_RANGE:
                rng = parse_range(value)
                if rng is None:
                    other.append(p)
                else:
                    factor = to_unit(1.0, unit, "A") if normalize_unit(unit) else 1.0
                    put("setting_range_min_a", rng[0] * (factor or 1.0), p)
                    put("setting_range_max_a", rng[1] * (factor or 1.0), p)
            elif key is SpecKey.CROSS_SECTION:
                cores, section = _parse_cable_section(value)
                put("cores_count", cores, p)
                put("cross_section_mm2", section, p)
            elif key is SpecKey.CORES:
                put("cores_count", parse_int(value), p)
            elif key is SpecKey.CABLE_TYPE:
                put("cable_type", value, p)
            elif key is SpecKey.LENGTH:
                put("length_m", value_in_unit(value, unit or "m", "m"), p)
            elif key is SpecKey.IP_RATING:
                put("ip_rating", _normalize_ip(value), p)
            elif key is SpecKey.WIDTH_MODULES:
                if normalize_unit(unit) == "mm":
                    mm = parse_number(value)
                    put("width_modules", round(mm / 18.0 * 2) / 2 if mm else None, p)
                    put("width_mm", mm, p)
                else:
                    put("width_modules", parse_number(value), p)
            elif key is SpecKey.DIMENSIONS:
                w, h, d = parse_dimensions_mm(value)
                put("width_mm", w, p)
                put("height_mm", h, p)
                put("depth_mm", d, p)
            elif key is SpecKey.MOUNTING:
                put("mounting", value, p)
            elif key is SpecKey.DIGITAL_INPUTS:
                put("digital_inputs", parse_int(value), p)
            elif key is SpecKey.DIGITAL_OUTPUTS:
                put("digital_outputs", parse_int(value), p)
            elif key is SpecKey.ANALOG_INPUTS:
                put("analog_inputs", parse_int(value), p)
            elif key is SpecKey.ANALOG_OUTPUTS:
                put("analog_outputs", parse_int(value), p)
            elif key is SpecKey.COMMUNICATION:
                parts = re.split(r"[;,/]", value)
                communication.extend(x.strip() for x in parts if x.strip())
            elif key is SpecKey.MEASURED_VARIABLE:
                put("measured_variable", value, p)
            elif key is SpecKey.MEASUREMENT_RANGE:
                put("measurement_range", combined, p)
            elif key is SpecKey.OUTPUT_SIGNAL:
                put("output_signal", combined, p)
            elif key is SpecKey.PROCESS_CONNECTION:
                put("process_connection", value, p)
            elif key is SpecKey.ACCURACY_CLASS:
                put("accuracy_class", value, p)
            elif key is SpecKey.COLOR:
                put("color", value.lower(), p)
            elif key is SpecKey.CONTACT_CONFIGURATION:
                no, nc = parse_contacts(value)
                put("contact_no", no, p)
                put("contact_nc", nc, p)
            elif key is SpecKey.LAMP_VOLTAGE:
                put("lamp_voltage_v", value_in_unit(value, unit, "V", prefer_max=True), p)
            elif key is SpecKey.MATERIAL:
                put("material", value, p)
            else:
                other.append(p)

        spec = cls(communication=unique_preserve_order(communication))
        rejected: list[TechnicalParameter] = []
        for field_name, field_value in data.items():
            try:
                setattr(spec, field_name, field_value)
            except ValueError:
                # Например poles=7: значение не проходит валидацию — сохраняем
                # исходный параметр в other, инженер увидит его в аудите.
                src = provenance[field_name]
                if src not in rejected:
                    rejected.append(src)
        spec.other = [*other, *rejected]
        return spec

    # --- сервисные методы ----------------------------------------------------

    def filled_fields(self) -> list[str]:
        result = []
        for name in type(self).model_fields:
            value = getattr(self, name)
            if name == "has_neutral":
                continue
            if value not in (None, [], ""):
                result.append(name)
        return result

    def is_empty(self) -> bool:
        return not self.filled_fields()

    def merged_with(self, other: TechnicalSpecs) -> TechnicalSpecs:
        """Дополняет пустые поля значениями из ``other`` (приоритет у self)."""
        merged = self.model_dump()
        for name in type(self).model_fields:
            mine = getattr(self, name)
            theirs = getattr(other, name)
            if name == "communication":
                merged[name] = unique_preserve_order([*mine, *theirs])
            elif name == "other":
                seen = {(p.key, p.name, p.value) for p in mine}
                merged[name] = [*mine, *[p for p in theirs if (p.key, p.name, p.value) not in seen]]
            elif name == "has_neutral":
                merged[name] = mine or theirs
            elif mine in (None, ""):
                merged[name] = theirs
        return TechnicalSpecs.model_validate(merged)

    def conflicts_with(self, other: TechnicalSpecs, rel_tol: float = 1e-6) -> list[str]:
        """Поля, заполненные в обоих наборах, но с разными значениями."""
        conflicts: list[str] = []
        for name in type(self).model_fields:
            if name in {"other", "communication", "has_neutral"}:
                continue
            a = getattr(self, name)
            b = getattr(other, name)
            if a in (None, "") or b in (None, ""):
                continue
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                if not math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=1e-9):
                    conflicts.append(name)
            elif str(a).strip().lower() != str(b).strip().lower():
                conflicts.append(name)
        return conflicts

    def to_search_text(self) -> str:
        """Компактная строка ТХ для fuzzy/векторного поиска: «C16 16A 3P+N 4.5kA 400V»."""
        tokens: list[str] = []
        if self.trip_curve and self.rated_current_a is not None:
            tokens.append(f"{self.trip_curve}{_fmt_num(self.rated_current_a)}")
        if self.rated_current_a is not None:
            tokens.append(f"{_fmt_num(self.rated_current_a)}A")
        if self.poles is not None:
            tokens.append(f"{self.poles}P" + ("+N" if self.has_neutral else ""))
        if self.breaking_capacity_ka is not None:
            tokens.append(f"{_fmt_num(self.breaking_capacity_ka)}kA")
        if self.residual_current_ma is not None:
            tokens.append(f"{_fmt_num(self.residual_current_ma)}mA")
        if self.rcd_type:
            tokens.append(f"тип {self.rcd_type}")
        if self.rated_voltage_v is not None:
            tokens.append(f"{_fmt_num(self.rated_voltage_v)}V")
        if self.current_type:
            tokens.append(self.current_type)
        if self.rated_power_kw is not None:
            tokens.append(f"{_fmt_num(self.rated_power_kw)}kW")
        if self.coil_voltage_v is not None:
            tokens.append(
                f"катушка {_fmt_num(self.coil_voltage_v)}V{(' ' + self.coil_current_type) if self.coil_current_type else ''}"
            )
        if self.main_contacts:
            tokens.append(self.main_contacts)
        if self.aux_contacts_no or self.aux_contacts_nc:
            tokens.append(f"{self.aux_contacts_no or 0}NO+{self.aux_contacts_nc or 0}NC")
        if self.utilization_category:
            tokens.append(self.utilization_category)
        if self.setting_range_min_a is not None and self.setting_range_max_a is not None:
            tokens.append(f"{_fmt_num(self.setting_range_min_a)}-{_fmt_num(self.setting_range_max_a)}A")
        if self.cable_type:
            tokens.append(self.cable_type)
        if self.cores_count and self.cross_section_mm2:
            tokens.append(f"{self.cores_count}x{_fmt_num(self.cross_section_mm2)}")
        elif self.cross_section_mm2:
            tokens.append(f"{_fmt_num(self.cross_section_mm2)}mm2")
        if self.ip_rating:
            tokens.append(self.ip_rating)
        if self.width_modules:
            tokens.append(f"{_fmt_num(self.width_modules)} мод.")
        if self.width_mm and self.height_mm:
            dims = [self.width_mm, self.height_mm] + ([self.depth_mm] if self.depth_mm else [])
            tokens.append("x".join(_fmt_num(d) for d in dims) + "мм")
        io = [
            ("DI", self.digital_inputs),
            ("DO", self.digital_outputs),
            ("AI", self.analog_inputs),
            ("AO", self.analog_outputs),
        ]
        tokens.extend(f"{n}{label}" for label, n in io if n)
        tokens.extend(self.communication)
        for attr in (
            "measured_variable",
            "measurement_range",
            "output_signal",
            "process_connection",
            "accuracy_class",
            "color",
            "mounting",
            "material",
        ):
            val = getattr(self, attr)
            if val:
                tokens.append(str(val))
        if self.contact_no or self.contact_nc:
            tokens.append(f"{self.contact_no or 0}NO+{self.contact_nc or 0}NC")
        if self.lamp_voltage_v is not None:
            tokens.append(f"лампа {_fmt_num(self.lamp_voltage_v)}V")
        tokens.extend(f"{p.name or p.key}: {p.value}{(' ' + p.unit) if p.unit else ''}" for p in self.other)
        return " ".join(t for t in tokens if t)


_CYR_TO_LAT_UPPER = str.maketrans(
    {"А": "A", "В": "B", "С": "C", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P", "Т": "T", "Х": "X", "І": "I"}
)


def _parse_cable_section(value: str) -> tuple[int | None, float | None]:
    """«5x10» -> (5, 10.0); «4х95+1х50» -> (4, 95.0); «2,5» -> (None, 2.5)."""
    text = value.replace(",", ".")
    text = re.sub(r"[хХ×*]", "x", text)
    m = re.search(r"(\d+)\s*x\s*(\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)
    if m:
        return int(m.group(1)), float(m.group(2))
    return None, parse_number(text)


def _normalize_ip(value: str) -> str:
    """«ip 54», «ІР54» (кириллица), «54» -> «IP54»."""
    text = value.upper().translate(_CYR_TO_LAT_UPPER)
    m = re.search(r"IP\s*(\d{2}[A-Z]?)", text)
    if m:
        return f"IP{m.group(1)}"
    digits = re.search(r"\b(\d{2})\b", text)
    return f"IP{digits.group(1)}" if digits else text.strip()


# =============================================================================
# 5. Агент 1 — Vision & OCR Extractor
# =============================================================================


class SheetInfo(LLMContract):
    """Данные основной надписи (штампа) листа."""

    drawing_type: DrawingType = Field(description="Тип документа на листе.")
    document_code: str = Field(description="Шифр/обозначение документа (например «12-24-ЭМ»). "
                               "Пустая строка, если нет.")
    sheet_title: str = Field(description="Наименование листа из штампа.")
    sheet_number: str = Field(description="Номер листа. Пустая строка, если нет.")
    total_sheets: str = Field(description="Всего листов. Пустая строка, если нет.")
    revision: str = Field(description="Изменение/ревизия. Пустая строка, если нет.")
    organization: str = Field(description="Организация-разработчик. Пустая строка, если нет.")


class RawComponent(LLMContract):
    """Одна позиция оборудования, найденная на листе."""

    designation: str = Field(
        description=(
            "Позиционное обозначение дословно: «QF1», «-KM2», «=A1-QF3», «QF1…QF6», "
            "«XT1:1-24». Если в таблице одной строкой указан диапазон — запиши диапазон "
            "целиком. Пустая строка, если обозначения нет (например, корпус шкафа)."
        )
    )
    category: ComponentCategory = Field(description="Категория изделия.")
    name: str = Field(
        description="Наименование как в документе (например «Выключатель автоматический "
        "трёхполюсный»). Если наименования нет — краткое инженерное описание по графике."
    )
    type_designation: str = Field(
        description="Тип/серия/марка изделия: «ВА47-29», «iC60N», «LC1D09», «ПВ-2». "
        "Пустая строка, если не указан."
    )
    manufacturer: str = Field(description="Производитель, если указан. Иначе пустая строка.")
    article: str = Field(
        description="Артикул/код заказа производителя, если указан (например «A9F74316», "
        "«MVA20-3-016-C»). Иначе пустая строка. Не придумывай артикулы."
    )
    parameters: list[TechnicalParameter] = Field(
        description="Все технические параметры, прочитанные с листа для этой позиции."
    )
    quantity: float = Field(
        description="Количество. Для кабеля/провода — длина в метрах. Если в таблице "
        "указано количество — бери его; иначе посчитай УГО на схеме."
    )
    unit: UnitOfMeasure = Field(description="Единица измерения количества.")
    quantity_basis: QuantityBasis = Field(
        description="stated — количество указано явно; counted — посчитано по УГО/обозначениям; "
        "inferred — предположено (обязательно поясни в notes)."
    )
    source_kind: SourceKind = Field(description="Где на листе найдена позиция.")
    tile_ids: list[str] = Field(description="Идентификаторы тайлов, где видна позиция.")
    evidence: str = Field(
        description="Дословный фрагмент текста или краткое описание УГО, подтверждающее "
        "позицию (для аудита). Не более 200 символов."
    )
    readability: Readability = Field(description="Насколько уверенно прочитаны данные.")
    confidence: float = Field(description="Уверенность в корректности позиции от 0 до 1.")
    notes: str = Field(description="Комментарий: что не дочитано, допущения. Иначе пустая строка.")

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp_confidence(cls, v: Any) -> float:
        return clamp01(v)

    @field_validator("quantity", mode="before")
    @classmethod
    def _non_negative_quantity(cls, v: Any) -> float:
        num = parse_number(v) if not isinstance(v, (int, float)) else float(v)
        return max(0.0, num or 0.0)


class UnreadableRegion(LLMContract):
    tile_id: str = Field(description="Тайл, где находится проблемная область (или «overview»).")
    description: str = Field(description="Что именно не читается и где (ориентир на листе).")
    suspected_content: str = Field(description="Предположение, что там написано. Иначе пустая строка.")
    impact: Severity = Field(description="Насколько это влияет на спецификацию.")


class VisionPageExtraction(LLMContract):
    """Полный ответ Агента 1 по одной странице (обзор + набор тайлов)."""

    sheet: SheetInfo
    page_summary: str = Field(
        description="2–4 предложения: что изображено на листе (тип схемы, объект, "
        "основные узлы, номиналы вводов)."
    )
    components: list[RawComponent] = Field(description="Все найденные позиции оборудования.")
    unreadable_regions: list[UnreadableRegion] = Field(
        description="Области, которые не удалось прочитать уверенно."
    )
    cross_references: list[str] = Field(
        description="Ссылки на другие листы/документы («см. лист 5», «ведомость кабелей ЭМ.КЖ»)."
    )
    extraction_notes: str = Field(description="Общие замечания к листу. Иначе пустая строка.")


class SourceReference(SpecFlowModel):
    document_id: str
    file_name: str = ""
    page_number: int = Field(ge=1)
    source_kind: SourceKind
    tile_ids: list[str] = Field(default_factory=list)
    evidence: str = ""


class ExtractedComponent(SpecFlowModel):
    """Позиция после Агента 1, привязанная к документу и странице."""

    uid: str = Field(default_factory=lambda: new_uid("c"))
    designation_raw: str | None = None
    tags: list[str] = Field(default_factory=list, description="Раскрытые позиционные обозначения.")
    category: ComponentCategory
    name: str
    type_designation: str | None = None
    manufacturer: str | None = None
    article: str | None = None
    parameters: list[TechnicalParameter] = Field(default_factory=list)
    specs: TechnicalSpecs = Field(default_factory=TechnicalSpecs)
    quantity: float = Field(ge=0)
    unit: UnitOfMeasure = UnitOfMeasure.PCS
    quantity_basis: QuantityBasis = QuantityBasis.STATED
    sources: list[SourceReference] = Field(default_factory=list)
    readability: Readability = Readability.CLEAR
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: str | None = None

    @field_validator("designation_raw", "type_designation", "manufacturer", "article", "notes", mode="before")
    @classmethod
    def _empty_strings_to_none(cls, v: Any) -> Any:
        return _empty_to_none(v)

    @classmethod
    def from_raw(
        cls,
        raw: RawComponent,
        *,
        document_id: str,
        page_number: int,
        file_name: str = "",
    ) -> ExtractedComponent:
        tags = expand_designations(raw.designation)
        quantity = raw.quantity
        if quantity <= 0 and tags:
            quantity = float(len(tags))
        elif quantity <= 0:
            quantity = 1.0
        return cls(
            designation_raw=raw.designation,
            tags=tags,
            category=raw.category,
            name=raw.name or raw.category.label_ru,
            type_designation=raw.type_designation,
            manufacturer=raw.manufacturer,
            article=raw.article,
            parameters=list(raw.parameters),
            specs=TechnicalSpecs.from_parameters(raw.parameters),
            quantity=quantity,
            unit=raw.unit,
            quantity_basis=raw.quantity_basis,
            sources=[
                SourceReference(
                    document_id=document_id,
                    file_name=file_name,
                    page_number=page_number,
                    source_kind=raw.source_kind,
                    tile_ids=list(raw.tile_ids),
                    evidence=raw.evidence,
                )
            ],
            readability=raw.readability,
            confidence=raw.confidence,
            notes=raw.notes,
        )

    @property
    def page_numbers(self) -> list[int]:
        return sorted({s.page_number for s in self.sources})


class PageSheetRecord(SpecFlowModel):
    document_id: str
    page_number: int = Field(ge=1)
    sheet: SheetInfo
    page_summary: str = ""
    cross_references: list[str] = Field(default_factory=list)
    extraction_notes: str = ""


class UnreadableRegionRecord(SpecFlowModel):
    document_id: str
    page_number: int = Field(ge=1)
    tile_id: str
    description: str
    suspected_content: str = ""
    impact: Severity = Severity.WARNING


class ExtractedRawBOM(SpecFlowModel):
    """Выход Агента 1: «сырая» спецификация по всем загруженным документам."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    documents: list[PdfDocumentInfo] = Field(default_factory=list)
    pages: list[PageSheetRecord] = Field(default_factory=list)
    components: list[ExtractedComponent] = Field(default_factory=list)
    unreadable_regions: list[UnreadableRegionRecord] = Field(default_factory=list)
    failed_pages: list[PageFailure] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)

    def add_page_result(
        self,
        *,
        document_id: str,
        page_number: int,
        extraction: VisionPageExtraction,
        file_name: str = "",
    ) -> list[ExtractedComponent]:
        """Добавляет ответ Агента 1 по странице. Возвращает созданные позиции."""
        self.pages.append(
            PageSheetRecord(
                document_id=document_id,
                page_number=page_number,
                sheet=extraction.sheet,
                page_summary=extraction.page_summary,
                cross_references=list(extraction.cross_references),
                extraction_notes=extraction.extraction_notes,
            )
        )
        created = [
            ExtractedComponent.from_raw(
                raw, document_id=document_id, page_number=page_number, file_name=file_name
            )
            for raw in extraction.components
        ]
        self.components.extend(created)
        self.unreadable_regions.extend(
            UnreadableRegionRecord(
                document_id=document_id,
                page_number=page_number,
                tile_id=r.tile_id,
                description=r.description,
                suspected_content=r.suspected_content,
                impact=r.impact,
            )
            for r in extraction.unreadable_regions
        )
        return created

    def find_by_tag(self, tag: str) -> list[ExtractedComponent]:
        norm = normalize_designation(tag)
        return [c for c in self.components if norm in c.tags]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def component_count(self) -> int:
        return len(self.components)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def category_counts(self) -> dict[str, int]:
        return dict(Counter(c.category.value for c in self.components))


# =============================================================================
# 6. Агент 2 — Engineering Validator
# =============================================================================


class ItemIssue(LLMContract):
    issue_type: IssueType
    severity: Severity
    message: str = Field(description="Конкретная формулировка проблемы с номиналами и обозначениями.")


class DuplicateGroup(LLMContract):
    uids: list[str] = Field(description="uid позиций, описывающих одно и то же физическое изделие.")
    keep_uid: str = Field(description="uid позиции, которую оставить (самая полная по данным).")
    resolution: DuplicateResolution = Field(
        description="merge — это один и тот же аппарат на разных листах/в таблице; "
        "keep_separate — похожи, но это разные аппараты."
    )
    final_quantity: float = Field(description="Итоговое количество после объединения.")
    reason: str = Field(description="Обоснование: совпадение позиционных обозначений, ТХ, листов.")


class ItemReview(LLMContract):
    uid: str = Field(description="uid проверяемой позиции.")
    status: ReviewStatus = Field(
        description="ok — замечаний нет; corrected — данные исправлены (укажи исправления); "
        "needs_review — требуется решение инженера."
    )
    issues: list[ItemIssue] = Field(description="Найденные проблемы. Пустой список, если их нет.")
    corrected_parameters: list[TechnicalParameter] = Field(
        description="Только исправленные или достоверно восстановленные параметры. "
        "Пустой список, если исправлений нет."
    )
    corrected_quantity: float | None = Field(
        description="Исправленное количество или null, если количество верное."
    )
    review_comment: str = Field(
        description="Точный технический комментарий для инженера: что проверить и почему. "
        "Пустая строка при статусе ok."
    )


class AccessoryProposal(LLMContract):
    category: ComponentCategory
    name: str = Field(description="Наименование аксессуара (например «Заглушка торцевая для клемм 2,5 мм²»).")
    parameters: list[TechnicalParameter]
    quantity: float = Field(description="Количество с учётом запаса.")
    unit: UnitOfMeasure
    related_uids: list[str] = Field(description="uid основных позиций, для которых нужен аксессуар.")
    calculation_basis: str = Field(
        description="Формула/логика расчёта: «24 клеммы × 1 + 2 на группу = 26 шт.»."
    )
    confidence: float = Field(description="Уверенность от 0 до 1.")

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp(cls, v: Any) -> float:
        return clamp01(v)


class CustomerQuestion(LLMContract):
    related_uids: list[str] = Field(description="uid позиций, к которым относится вопрос.")
    question: str = Field(description="Вопрос заказчику в деловой форме, однозначный, с вариантами ответа.")
    reason: str = Field(description="Почему возник вопрос (что на чертеже неясно или противоречиво).")
    impact: Severity = Field(description="Влияние на стоимость/комплектацию.")
    assumed_answer: str = Field(
        description="Что заложено в расчёт по умолчанию до ответа заказчика."
    )


class ValidatorReview(LLMContract):
    """Полный ответ Агента 2."""

    duplicate_groups: list[DuplicateGroup]
    item_reviews: list[ItemReview] = Field(
        description="Ревью только тех позиций, где есть замечания или исправления."
    )
    accessories: list[AccessoryProposal] = Field(
        description="Монтажные аксессуары, не учтённые правилами комплектации."
    )
    questions: list[CustomerQuestion]
    general_findings: list[str] = Field(
        description="Замечания по проекту в целом (селективность, резерв, климат шкафа)."
    )
    summary: str = Field(description="Итог нормоконтроля в 3–5 предложениях.")


class ReviewNote(SpecFlowModel):
    issue_type: IssueType
    severity: Severity
    message: str
    author: str = "validator"


class EngineeringItem(SpecFlowModel):
    """Позиция инженерной спецификации после нормоконтроля."""

    uid: str = Field(default_factory=lambda: new_uid("e"))
    origin: ItemOrigin = ItemOrigin.EXTRACTED
    category: ComponentCategory
    name: str
    designation_raw: str | None = None
    tags: list[str] = Field(default_factory=list)
    type_designation: str | None = None
    manufacturer: str | None = None
    article: str | None = None
    parameters: list[TechnicalParameter] = Field(default_factory=list)
    specs: TechnicalSpecs = Field(default_factory=TechnicalSpecs)
    quantity: float = Field(ge=0)
    unit: UnitOfMeasure = UnitOfMeasure.PCS
    sources: list[SourceReference] = Field(default_factory=list)
    related_uids: list[str] = Field(default_factory=list)
    merged_from_uids: list[str] = Field(default_factory=list)
    calculation_basis: str | None = None
    review_status: ReviewStatus = ReviewStatus.OK
    review_notes: list[ReviewNote] = Field(default_factory=list)
    review_comment: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator(
        "designation_raw",
        "type_designation",
        "manufacturer",
        "article",
        "calculation_basis",
        "review_comment",
        mode="before",
    )
    @classmethod
    def _empty_strings_to_none(cls, v: Any) -> Any:
        return _empty_to_none(v)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def needs_review(self) -> bool:
        return self.review_status is ReviewStatus.NEEDS_REVIEW or any(
            n.severity is Severity.CRITICAL for n in self.review_notes
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_accessory(self) -> bool:
        return self.origin in (ItemOrigin.ACCESSORY_RULE, ItemOrigin.ACCESSORY_AI)

    @property
    def display_designation(self) -> str:
        if self.designation_raw:
            return self.designation_raw
        if len(self.tags) > 3:
            return f"{self.tags[0]}…{self.tags[-1]}"
        return ", ".join(self.tags)

    @classmethod
    def from_extracted(cls, c: ExtractedComponent) -> EngineeringItem:
        return cls(
            uid=c.uid,
            origin=ItemOrigin.EXTRACTED,
            category=c.category,
            name=c.name,
            designation_raw=c.designation_raw,
            tags=list(c.tags),
            type_designation=c.type_designation,
            manufacturer=c.manufacturer,
            article=c.article,
            parameters=list(c.parameters),
            specs=c.specs.model_copy(deep=True),
            quantity=c.quantity,
            unit=c.unit,
            sources=[s.model_copy() for s in c.sources],
            confidence=c.confidence,
            review_status=(
                ReviewStatus.NEEDS_REVIEW
                if c.readability is Readability.UNREADABLE
                else ReviewStatus.OK
            ),
            review_comment=c.notes,
        )

    @classmethod
    def from_accessory(cls, a: AccessoryProposal, origin: ItemOrigin = ItemOrigin.ACCESSORY_AI) -> EngineeringItem:
        return cls(
            uid=new_uid("a"),
            origin=origin,
            category=a.category,
            name=a.name,
            parameters=list(a.parameters),
            specs=TechnicalSpecs.from_parameters(a.parameters),
            quantity=max(0.0, a.quantity),
            unit=a.unit,
            related_uids=list(a.related_uids),
            calculation_basis=a.calculation_basis,
            confidence=a.confidence,
        )


class MergeRecord(SpecFlowModel):
    kept_uid: str
    merged_uids: list[str]
    final_quantity: float
    reason: str


class ValidatedEngineeringBOM(SpecFlowModel):
    """Выход Агента 2."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    documents: list[PdfDocumentInfo] = Field(default_factory=list)
    pages: list[PageSheetRecord] = Field(default_factory=list)
    items: list[EngineeringItem] = Field(default_factory=list)
    merges: list[MergeRecord] = Field(default_factory=list)
    questions: list[CustomerQuestion] = Field(default_factory=list)
    unreadable_regions: list[UnreadableRegionRecord] = Field(default_factory=list)
    general_findings: list[str] = Field(default_factory=list)
    summary: str = ""
    created_at: datetime = Field(default_factory=utc_now)

    @property
    def main_items(self) -> list[EngineeringItem]:
        return [i for i in self.items if not i.is_accessory]

    @property
    def accessories(self) -> list[EngineeringItem]:
        return [i for i in self.items if i.is_accessory]

    @property
    def items_needing_review(self) -> list[EngineeringItem]:
        return [i for i in self.items if i.needs_review]

    def item(self, uid: str) -> EngineeringItem:
        for i in self.items:
            if i.uid == uid:
                return i
        raise KeyError(f"Позиция {uid} не найдена")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def item_count(self) -> int:
        return len(self.items)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def needs_review_count(self) -> int:
        return len(self.items_needing_review)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def accessory_count(self) -> int:
        return len(self.accessories)


# =============================================================================
# 7. Агент 3 — Catalog & SKU Matcher
# =============================================================================

_CURRENCY_ALIASES = {
    "РУБ": "RUB", "РУБ.": "RUB", "RUR": "RUB", "₽": "RUB", "Р": "RUB",
    "$": "USD", "US$": "USD", "ДОЛЛ": "USD",
    "€": "EUR", "ЕВРО": "EUR",
    "₪": "ILS", "NIS": "ILS", "ШЕКЕЛЬ": "ILS", "ש\"ח": "ILS", "ש״ח": "ILS",
    "ТГ": "KZT", "₸": "KZT",
    "ГРН": "UAH", "₴": "UAH",
    "BYR": "BYN",
}


def normalize_currency(value: str | None, default: str = "USD") -> str:
    if not value:
        return default
    v = str(value).strip().upper()
    v = _CURRENCY_ALIASES.get(v, v)
    if len(v) != 3 or not v.isalpha():
        raise ValueError(f"Неизвестная валюта: {value!r}")
    return v


class CatalogItem(SpecFlowModel):
    """Строка прайс-листа поставщика (колонки Brand, SKU, Name, Technical_Specs, …)."""

    catalog_uid: str = Field(default="", description="Стабильный id: hash(supplier|brand|sku).")
    supplier: str = ""
    brand: str
    sku: str = Field(min_length=1)
    name: str
    technical_specs: str = ""
    base_price: Decimal = Field(ge=0)
    currency: str = "USD"
    unit: UnitOfMeasure = UnitOfMeasure.PCS
    pack_quantity: float = Field(
        default=1.0,
        gt=0,
        description="Сколько единиц BOM в одной единице продажи (упаковка НШВИ 1000 шт., "
        "кабель-канал 2 м в штуке).",
    )
    lead_time_days: int | None = Field(default=None, ge=0)
    lead_time_raw: str | None = None
    category_hint: ComponentCategory | None = None
    source_file: str | None = None
    source_row: int | None = None
    imported_at: datetime = Field(default_factory=utc_now)

    @field_validator("currency", mode="before")
    @classmethod
    def _currency(cls, v: Any) -> str:
        return normalize_currency(v)

    @field_validator("base_price", mode="before")
    @classmethod
    def _price(cls, v: Any) -> Decimal:
        d = to_decimal(v)
        if d is None:
            raise ValueError(f"Некорректная цена: {v!r}")
        return d

    @field_validator("sku", "brand", mode="after")
    @classmethod
    def _strip_inner(cls, v: str) -> str:
        return " ".join(v.split())

    @model_validator(mode="after")
    def _uid(self) -> CatalogItem:
        if not self.catalog_uid:
            key = f"{self.supplier.lower()}|{self.brand.lower()}|{self.sku.lower()}"
            self.__dict__["catalog_uid"] = "k_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        return self

    @property
    def search_text(self) -> str:
        return " ".join(x for x in (self.brand, self.sku, self.name, self.technical_specs) if x)

    @property
    def normalized_sku(self) -> str:
        return "".join(ch for ch in self.sku.upper() if ch.isalnum())


class CandidateScores(SpecFlowModel):
    exact_sku: bool = False
    fuzzy_name: float = Field(default=0.0, ge=0.0, le=100.0)
    fuzzy_sku: float = Field(default=0.0, ge=0.0, le=100.0)
    vector_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    spec_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    combined: float = Field(default=0.0, ge=0.0, le=1.0)


class CatalogCandidate(SpecFlowModel):
    rank: int = Field(ge=1)
    item: CatalogItem
    scores: CandidateScores = Field(default_factory=CandidateScores)
    retrieval_methods: list[RetrievalMethod] = Field(default_factory=list)


class MatchDecision(LLMContract):
    item_uid: str = Field(description="uid позиции спецификации.")
    selected_catalog_uid: str = Field(
        description="catalog_uid выбранного кандидата. Пустая строка, если ни один не подходит."
    )
    match_type: MatchType = Field(
        description="exact_sku — совпал артикул; exact_specs — тот же бренд/серия и все "
        "ключевые ТХ; analog — другой бренд, ТХ не хуже требуемых; partial — есть "
        "отклонения ТХ (обязательно перечисли); not_found — подходящих нет."
    )
    confidence: float = Field(description="Уверенность от 0 до 1.")
    justification: str = Field(description="Почему выбран кандидат: какие ТХ сверены.")
    spec_differences: list[str] = Field(
        description="Отличия ТХ кандидата от требуемых («Icu 6 кА вместо 10 кА»)."
    )
    needs_review: bool = Field(description="true, если выбор должен подтвердить инженер.")

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp(cls, v: Any) -> float:
        return clamp01(v)


class MatchBatchResult(LLMContract):
    decisions: list[MatchDecision]


class MatchResult(SpecFlowModel):
    match_type: MatchType = MatchType.NOT_FOUND
    selected: CatalogItem | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    justification: str = ""
    spec_differences: list[str] = Field(default_factory=list)
    needs_review: bool = True
    decided_by: Literal["rule", "llm", "manual"] = "rule"

    @model_validator(mode="after")
    def _consistency(self) -> MatchResult:
        if self.selected is None and self.match_type is not MatchType.NOT_FOUND:
            raise ValueError("match_type должен быть not_found, если кандидат не выбран")
        if self.selected is not None and self.match_type is MatchType.NOT_FOUND:
            raise ValueError("Выбран кандидат, но match_type=not_found")
        return self


class PricedItem(EngineeringItem):
    """Позиция спецификации с подобранным артикулом и ценой."""

    candidates: list[CatalogCandidate] = Field(default_factory=list)
    match: MatchResult = Field(default_factory=MatchResult)
    unit_price_base: Decimal | None = Field(
        default=None,
        description="Цена за единицу продажи в базовой валюте проекта (после конвертации).",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sku(self) -> str | None:
        return self.match.selected.sku if self.match.selected else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def brand(self) -> str | None:
        return self.match.selected.brand if self.match.selected else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def purchase_quantity(self) -> float:
        """Количество в единицах продажи: 1500 НШВИ при упаковке 1000 -> 2 уп."""
        sel = self.match.selected
        if sel is None or sel.pack_quantity == 1.0:
            return self.quantity
        return float(math.ceil(self.quantity / sel.pack_quantity - 1e-9))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def line_total_base(self) -> Decimal | None:
        if self.unit_price_base is None:
            return None
        return money(self.unit_price_base * to_decimal(self.purchase_quantity, Decimal(0)))

    @classmethod
    def from_engineering(
        cls,
        item: EngineeringItem,
        *,
        candidates: list[CatalogCandidate],
        match: MatchResult,
        unit_price_base: Decimal | None,
    ) -> PricedItem:
        return cls(
            **item.model_dump(),
            candidates=candidates,
            match=match,
            unit_price_base=unit_price_base,
        )


class PricedBOM(SpecFlowModel):
    """Выход Агента 3."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    documents: list[PdfDocumentInfo] = Field(default_factory=list)
    pages: list[PageSheetRecord] = Field(default_factory=list)
    items: list[PricedItem] = Field(default_factory=list)
    questions: list[CustomerQuestion] = Field(default_factory=list)
    unreadable_regions: list[UnreadableRegionRecord] = Field(default_factory=list)
    general_findings: list[str] = Field(default_factory=list)
    validator_summary: str = ""
    base_currency: str = "USD"
    exchange_rates: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Курс: сколько единиц базовой валюты за 1 единицу валюты прайса.",
    )
    catalog_version: str | None = None
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("base_currency", mode="before")
    @classmethod
    def _currency(cls, v: Any) -> str:
        return normalize_currency(v)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def matched_count(self) -> int:
        return sum(1 for i in self.items if i.match.selected is not None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def unmatched_count(self) -> int:
        return sum(1 for i in self.items if i.match.selected is None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def analog_count(self) -> int:
        return sum(1 for i in self.items if i.match.match_type is MatchType.ANALOG)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def materials_total_base(self) -> Decimal:
        return money(sum((i.line_total_base or Decimal(0) for i in self.items), Decimal(0)))


# =============================================================================
# 8. Агент 4 — Commercial Estimator & Excel Builder
# =============================================================================


class CommercialTerms(SpecFlowModel):
    validity_days: int = Field(default=14, ge=1, le=365)
    payment_terms: str = "Предоплата 50%, 50% по факту готовности к отгрузке"
    delivery_terms: str = "Самовывоз со склада исполнителя"
    warranty_months: int = Field(default=12, ge=0, le=120)
    lead_time_note: str = "Срок изготовления уточняется после подтверждения спецификации"
    additional_notes: list[str] = Field(default_factory=list)


class EstimateSettings(SpecFlowModel):
    """Настройки коммерческого расчёта из UI."""

    base_currency: str = "USD"
    material_markup_pct: Decimal = Field(default=Decimal("25"), ge=0, le=1000)
    labor_rate_per_hour: Decimal = Field(default=Decimal("50"), ge=0)
    contingency_pct: Decimal = Field(default=Decimal("5"), ge=0, le=100)
    vat_pct: Decimal = Field(default=Decimal("18"), ge=0, le=100)
    include_vat: bool = True
    include_items_needing_review: bool = True
    exchange_rates: dict[str, Decimal] = Field(default_factory=dict)
    customer_name: str = ""
    project_name: str = ""
    contractor_name: str = ""
    quote_number: str = ""
    terms: CommercialTerms = Field(default_factory=CommercialTerms)

    @field_validator("base_currency", mode="before")
    @classmethod
    def _currency(cls, v: Any) -> str:
        return normalize_currency(v)

    @field_validator("exchange_rates", mode="before")
    @classmethod
    def _rates(cls, v: Any) -> dict[str, Decimal]:
        if not v:
            return {}
        out: dict[str, Decimal] = {}
        for k, rate in dict(v).items():
            d = to_decimal(rate)
            if d is None or d <= 0:
                raise ValueError(f"Некорректный курс для {k}: {rate!r}")
            out[normalize_currency(k)] = d
        return out

    def rate_to_base(self, currency: str) -> Decimal:
        cur = normalize_currency(currency)
        if cur == self.base_currency:
            return Decimal(1)
        if cur not in self.exchange_rates:
            raise KeyError(
                f"Нет курса {cur}->{self.base_currency}. Укажите курс в настройках расчёта."
            )
        return self.exchange_rates[cur]


class LaborNorm(SpecFlowModel):
    category: ComponentCategory
    operation: str
    hours_per_unit: Decimal = Field(ge=0)
    unit: UnitOfMeasure = UnitOfMeasure.PCS
    source: NormSource = NormSource.DEFAULT_TABLE


class LaborAssessmentItem(LLMContract):
    item_uid: str
    operation: str = Field(description="Состав работ: «установка на DIN-рейку, подключение 6 проводов».")
    hours_per_unit: float = Field(description="Норма времени на единицу, часов.")
    rationale: str = Field(description="Обоснование нормы.")


class LaborAssessment(LLMContract):
    """Ответ Агента 4: нормы для позиций без табличной нормы + общие работы."""

    items: list[LaborAssessmentItem]
    assembly_overhead_hours: float = Field(
        description="Общие работы на щит: разметка, монтаж рейки и каналов, маркировка, "
        "прозвонка, испытания, документация. Часов."
    )
    overhead_rationale: str
    commercial_assumptions: list[str] = Field(description="Допущения, которые войдут в КП.")
    exclusions: list[str] = Field(description="Что не входит в стоимость (монтаж на объекте, ПНР…).")


class EstimateLine(SpecFlowModel):
    position: int = Field(ge=1)
    item_uid: str
    designation: str = ""
    name: str
    category: ComponentCategory
    origin: ItemOrigin = ItemOrigin.EXTRACTED
    sku: str | None = None
    brand: str | None = None
    match_type: MatchType = MatchType.NOT_FOUND
    quantity: Decimal = Field(ge=0)
    unit: UnitOfMeasure = UnitOfMeasure.PCS
    purchase_unit_price: Decimal = Field(default=Decimal(0), ge=0)
    markup_pct: Decimal = Field(default=Decimal(0), ge=0)
    labor_hours_per_unit: Decimal = Field(default=Decimal(0), ge=0)
    labor_rate: Decimal = Field(default=Decimal(0), ge=0)
    labor_norm_source: NormSource = NormSource.DEFAULT_TABLE
    needs_review: bool = False
    note: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def purchase_total(self) -> Decimal:
        return money(self.purchase_unit_price * self.quantity)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sale_unit_price(self) -> Decimal:
        return money(self.purchase_unit_price * (Decimal(1) + self.markup_pct / Decimal(100)))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sale_total(self) -> Decimal:
        return money(self.sale_unit_price * self.quantity)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def labor_hours_total(self) -> Decimal:
        return (self.labor_hours_per_unit * self.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def labor_cost(self) -> Decimal:
        return money(self.labor_hours_total * self.labor_rate)


class EstimateTotals(SpecFlowModel):
    currency: str
    materials_purchase: Decimal
    materials_sale: Decimal
    materials_margin: Decimal
    labor_hours: Decimal
    labor_cost: Decimal
    contingency_amount: Decimal
    subtotal_ex_vat: Decimal
    vat_amount: Decimal
    total_inc_vat: Decimal

    @computed_field  # type: ignore[prop-decorator]
    @property
    def materials_margin_pct(self) -> Decimal:
        if self.materials_sale == 0:
            return Decimal(0)
        return (self.materials_margin / self.materials_sale * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    @classmethod
    def compute(
        cls,
        lines: list[EstimateLine],
        settings: EstimateSettings,
        overhead_hours: Decimal = Decimal(0),
    ) -> EstimateTotals:
        """Итоги КП. Excel дублирует расчёт формулами — суммы обязаны совпасть."""
        considered = [ln for ln in lines if settings.include_items_needing_review or not ln.needs_review]
        materials_purchase = money(sum((ln.purchase_total for ln in considered), Decimal(0)))
        materials_sale = money(sum((ln.sale_total for ln in considered), Decimal(0)))
        line_hours = sum((ln.labor_hours_total for ln in considered), Decimal(0))
        labor_hours = (line_hours + overhead_hours).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        labor_cost = money(
            sum((ln.labor_cost for ln in considered), Decimal(0))
            + overhead_hours * settings.labor_rate_per_hour
        )
        base = materials_sale + labor_cost
        contingency = money(base * settings.contingency_pct / Decimal(100))
        subtotal = money(base + contingency)
        vat = money(subtotal * settings.vat_pct / Decimal(100)) if settings.include_vat else Decimal("0.00")
        return cls(
            currency=settings.base_currency,
            materials_purchase=materials_purchase,
            materials_sale=materials_sale,
            materials_margin=money(materials_sale - materials_purchase),
            labor_hours=labor_hours,
            labor_cost=labor_cost,
            contingency_amount=contingency,
            subtotal_ex_vat=subtotal,
            vat_amount=vat,
            total_inc_vat=money(subtotal + vat),
        )


class CommercialEstimate(SpecFlowModel):
    """Выход Агента 4 (до экспорта в Excel)."""

    schema_version: str = SCHEMA_VERSION
    run_id: str
    settings: EstimateSettings
    lines: list[EstimateLine] = Field(default_factory=list)
    labor_norms_used: list[LaborNorm] = Field(default_factory=list)
    overhead_hours: Decimal = Field(default=Decimal(0), ge=0)
    overhead_rationale: str = ""
    totals: EstimateTotals
    assumptions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    questions: list[CustomerQuestion] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ExcelExportResult(SpecFlowModel):
    path: Path
    sheet_names: list[str]
    row_counts: dict[str, int] = Field(default_factory=dict)
    file_size_bytes: int = Field(ge=0)
    generated_at: datetime = Field(default_factory=utc_now)


# =============================================================================
# 9. Наблюдаемость: токены, стоимость, события, прогон
# =============================================================================


class TokenUsage(SpecFlowModel):
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cache_creation_input_tokens: int = Field(default=0, ge=0)
    cache_read_input_tokens: int = Field(default=0, ge=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_input_tokens
            + self.cache_read_input_tokens
        )

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_creation_input_tokens=self.cache_creation_input_tokens + other.cache_creation_input_tokens,
            cache_read_input_tokens=self.cache_read_input_tokens + other.cache_read_input_tokens,
        )

    @classmethod
    def from_api(cls, usage: Any) -> TokenUsage:
        """Из объекта ``response.usage`` SDK anthropic (поля могут быть None)."""
        if usage is None:
            return cls()

        def get(name: str) -> int:
            value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, None)
            return int(value or 0)

        return cls(
            input_tokens=get("input_tokens"),
            output_tokens=get("output_tokens"),
            cache_creation_input_tokens=get("cache_creation_input_tokens"),
            cache_read_input_tokens=get("cache_read_input_tokens"),
        )


class LLMCallRecord(SpecFlowModel):
    call_id: str = Field(default_factory=lambda: new_uid("call"))
    stage: PipelineStage
    agent_name: str
    model_requested: str
    model_served: str | None = None
    purpose: str = ""
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    duration_s: float = 0.0
    attempts: int = Field(default=1, ge=1)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost_usd: Decimal = Field(default=Decimal(0), ge=0)
    cost_is_estimate: bool = False
    stop_reason: str | None = None
    request_id: str | None = None
    success: bool = True
    error: str | None = None


class StageReport(SpecFlowModel):
    stage: PipelineStage
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    calls: list[LLMCallRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def usage(self) -> TokenUsage:
        total = TokenUsage()
        for c in self.calls:
            total = total + c.usage
        return total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cost_usd(self) -> Decimal:
        return sum((c.cost_usd for c in self.calls), Decimal(0)).quantize(RATE_QUANT)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration_s(self) -> float:
        if self.started_at and self.finished_at:
            return round((self.finished_at - self.started_at).total_seconds(), 3)
        return 0.0


class PipelineEvent(SpecFlowModel):
    """Событие для live-лога в UI (и для файла журнала прогона)."""

    event_id: str = Field(default_factory=lambda: new_uid("ev"))
    ts: datetime = Field(default_factory=utc_now)
    stage: PipelineStage
    level: EventLevel = EventLevel.INFO
    message: str
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
    details: dict[str, Any] = Field(default_factory=dict)


class PipelineRun(SpecFlowModel):
    run_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6])
    created_at: datetime = Field(default_factory=utc_now)
    status: StageStatus = StageStatus.PENDING
    input_pdfs: list[Path] = Field(default_factory=list)
    price_lists: list[Path] = Field(default_factory=list)
    estimate_settings: EstimateSettings | None = None
    stages: dict[PipelineStage, StageReport] = Field(
        default_factory=lambda: {s: StageReport(stage=s) for s in PipelineStage}
    )
    output_xlsx: Path | None = None
    artifacts: dict[str, Path] = Field(default_factory=dict)
    error: str | None = None

    def stage(self, stage: PipelineStage) -> StageReport:
        return self.stages[stage]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_usage(self) -> TokenUsage:
        total = TokenUsage()
        for report in self.stages.values():
            total = total + report.usage
        return total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_cost_usd(self) -> Decimal:
        return sum((r.cost_usd for r in self.stages.values()), Decimal(0)).quantize(RATE_QUANT)
