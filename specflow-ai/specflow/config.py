"""
Конфигурация SpecFlow AI.

* ``Settings`` — все параметры из ``.env`` (pydantic-settings) с валидацией.
* ``MODEL_REGISTRY`` — цены моделей Claude и лимиты Vision для расчёта
  стоимости прогона и размера тайлов чертежей.
* ``compute_cost`` — стоимость вызова в долларах по ``TokenUsage``.
* ``configure_logging`` — консоль + ротируемый файл журнала (UTF-8, Windows-safe).

Цены — публичный прайс Anthropic API (за 1 млн токенов, USD) на момент
разработки. Если Anthropic изменит цены, правится только этот файл.
"""

from __future__ import annotations

import contextlib
import logging
import logging.handlers
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from specflow.exceptions import ConfigurationError
from specflow.schemas import (
    CommercialTerms,
    EstimateSettings,
    PdfProcessingOptions,
    RenderColorspace,
    TokenUsage,
    normalize_currency,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EffortLevel = Literal["low", "medium", "high", "xhigh", "max"]

# =============================================================================
# Реестр моделей Claude
# =============================================================================


class ModelProfile(BaseModel):
    """Цены и возможности модели, важные для пайплайна."""

    model_config = ConfigDict(frozen=True)

    model_id: str
    display_name: str
    input_usd_per_mtok: Decimal
    output_usd_per_mtok: Decimal
    cache_write_usd_per_mtok: Decimal
    cache_read_usd_per_mtok: Decimal
    # Vision: картинки больше лимита API уменьшает сам — мелкий текст чертежа
    # теряется. Поэтому тайлы режутся строго под эти лимиты.
    vision_max_edge_px: int
    vision_max_pixels: int
    # adaptive_explicit — нужно явно передать thinking={"type": "adaptive"};
    # always_on — мышление всегда включено, глубина управляется только effort.
    thinking_mode: Literal["adaptive_explicit", "always_on"]
    supports_forced_tool_choice: bool
    default_effort: EffortLevel
    # Ступенчатая цена (длинный промпт дороже), если есть.
    long_context_threshold_tokens: int | None = None
    long_input_usd_per_mtok: Decimal | None = None
    long_output_usd_per_mtok: Decimal | None = None

    @property
    def vision_tile_side_px(self) -> int:
        return int(min(self.vision_max_edge_px, math.isqrt(self.vision_max_pixels)))


def _p(value: str) -> Decimal:
    return Decimal(value)


MODEL_REGISTRY: dict[str, ModelProfile] = {
    profile.model_id: profile
    for profile in (
        ModelProfile(
            model_id="claude-opus-4-6",
            display_name="Claude Opus 4.6",
            input_usd_per_mtok=_p("5.00"),
            output_usd_per_mtok=_p("25.00"),
            cache_write_usd_per_mtok=_p("6.25"),
            cache_read_usd_per_mtok=_p("0.50"),
            vision_max_edge_px=1568,
            vision_max_pixels=1_150_000,
            thinking_mode="adaptive_explicit",
            supports_forced_tool_choice=True,
            default_effort="high",
        ),
        ModelProfile(
            model_id="claude-sonnet-4-6",
            display_name="Claude Sonnet 4.6",
            input_usd_per_mtok=_p("3.00"),
            output_usd_per_mtok=_p("15.00"),
            cache_write_usd_per_mtok=_p("3.75"),
            cache_read_usd_per_mtok=_p("0.30"),
            vision_max_edge_px=1568,
            vision_max_pixels=1_150_000,
            thinking_mode="adaptive_explicit",
            supports_forced_tool_choice=True,
            default_effort="high",
        ),
        ModelProfile(
            model_id="claude-opus-5-5",
            display_name="Claude Opus 5.5",
            input_usd_per_mtok=_p("4.00"),
            output_usd_per_mtok=_p("20.00"),
            cache_write_usd_per_mtok=_p("5.00"),
            cache_read_usd_per_mtok=_p("0.20"),
            vision_max_edge_px=2576,
            vision_max_pixels=3_750_000,
            thinking_mode="always_on",
            supports_forced_tool_choice=False,
            default_effort="medium",
        ),
        ModelProfile(
            model_id="claude-sonnet-5-5",
            display_name="Claude Sonnet 5.5",
            input_usd_per_mtok=_p("2.00"),
            output_usd_per_mtok=_p("10.00"),
            cache_write_usd_per_mtok=_p("2.50"),
            cache_read_usd_per_mtok=_p("0.20"),
            vision_max_edge_px=2576,
            vision_max_pixels=3_750_000,
            thinking_mode="adaptive_explicit",
            supports_forced_tool_choice=False,
            default_effort="high",
        ),
        ModelProfile(
            model_id="claude-haiku-5-5",
            display_name="Claude Haiku 5.5",
            input_usd_per_mtok=_p("0.10"),
            output_usd_per_mtok=_p("0.50"),
            # Кэш — по стандартным множителям 1.25× (запись) и 0.1× (чтение).
            cache_write_usd_per_mtok=_p("0.125"),
            cache_read_usd_per_mtok=_p("0.01"),
            # Лимиты Vision для Haiku 5.5 берём консервативные (как у 4.6):
            # меньший тайл всегда безопасен, просто тайлов больше.
            vision_max_edge_px=1568,
            vision_max_pixels=1_150_000,
            thinking_mode="adaptive_explicit",
            supports_forced_tool_choice=True,
            default_effort="medium",
            long_context_threshold_tokens=100_000,
            long_input_usd_per_mtok=_p("0.50"),
            long_output_usd_per_mtok=_p("2.50"),
        ),
    )
}

# Для неизвестной модели считаем по самому дорогому тарифу из реестра и
# помечаем стоимость как оценочную — бюджет прогона не будет занижен.
_FALLBACK_PROFILE = MODEL_REGISTRY["claude-opus-4-6"]

USD_QUANT = Decimal("0.000001")


def get_model_profile(model_id: str) -> tuple[ModelProfile, bool]:
    """Профиль модели и флаг «найден в реестре».

    Суффиксы вида ``[1m]`` отбрасываются.
    """
    key = model_id.split("[", 1)[0].strip()
    profile = MODEL_REGISTRY.get(key)
    if profile is not None:
        return profile, True
    return _FALLBACK_PROFILE, False


def compute_cost(usage: TokenUsage, model_id: str) -> tuple[Decimal, bool]:
    """Стоимость вызова в USD и флаг «оценка» (модель не найдена в реестре)."""
    profile, known = get_model_profile(model_id)
    in_price = profile.input_usd_per_mtok
    out_price = profile.output_usd_per_mtok
    cw_price = profile.cache_write_usd_per_mtok
    cr_price = profile.cache_read_usd_per_mtok

    prompt_tokens = usage.input_tokens + usage.cache_creation_input_tokens + usage.cache_read_input_tokens
    if (
        profile.long_context_threshold_tokens is not None
        and prompt_tokens > profile.long_context_threshold_tokens
        and profile.long_input_usd_per_mtok is not None
        and profile.long_output_usd_per_mtok is not None
    ):
        ratio = profile.long_input_usd_per_mtok / in_price
        in_price = profile.long_input_usd_per_mtok
        out_price = profile.long_output_usd_per_mtok
        cw_price = cw_price * ratio
        cr_price = cr_price * ratio

    total = (
        Decimal(usage.input_tokens) * in_price
        + Decimal(usage.output_tokens) * out_price
        + Decimal(usage.cache_creation_input_tokens) * cw_price
        + Decimal(usage.cache_read_input_tokens) * cr_price
    ) / Decimal(1_000_000)
    return total.quantize(USD_QUANT, rounding=ROUND_HALF_UP), not known


def estimate_image_input_cost(image_tokens: int, model_id: str) -> Decimal:
    """Оценка стоимости отправки изображений (только вход, без ответа)."""
    cost, _ = compute_cost(TokenUsage(input_tokens=image_tokens), model_id)
    return cost


# =============================================================================
# Settings (.env)
# =============================================================================


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Anthropic -----------------------------------------------------------
    anthropic_api_key: SecretStr | None = None
    anthropic_base_url: str | None = None

    model_extractor: str = "claude-opus-4-6"
    model_validator: str = "claude-opus-4-6"
    model_matcher: str = "claude-sonnet-4-6"
    model_estimator: str = "claude-sonnet-4-6"

    effort_extractor: EffortLevel = "high"
    effort_validator: EffortLevel = "high"
    effort_matcher: EffortLevel = "medium"
    effort_estimator: EffortLevel = "medium"

    llm_max_output_tokens: int = Field(default=32_000, ge=1_024, le=128_000)
    llm_timeout_s: float = Field(default=600.0, gt=0)
    llm_max_retries: int = Field(default=5, ge=0, le=20)
    llm_retry_base_delay_s: float = Field(default=2.0, gt=0)
    llm_retry_max_delay_s: float = Field(default=60.0, gt=0)
    llm_max_concurrency: int = Field(default=4, ge=1, le=64)
    vision_tiles_per_request: int = Field(default=12, ge=1, le=100)
    run_budget_usd: Decimal = Field(default=Decimal("20"), gt=0)

    # --- PDF -----------------------------------------------------------------
    pdf_render_dpi: int = Field(default=300, ge=72, le=600)
    pdf_tile_overlap_px: int = Field(default=180, ge=0)
    pdf_colorspace: RenderColorspace = RenderColorspace.RGB
    pdf_save_full_page: bool = True
    pdf_full_page_max_megapixels: float = Field(default=80.0, gt=0)
    pdf_extract_tables: bool = True
    pdf_table_max_vector_paths: int = Field(default=60_000, ge=0)
    pdf_max_pages: int = Field(default=60, ge=1)
    pdf_workers: int = Field(default=0, ge=0, le=64)
    pdf_jpeg_quality: int = Field(default=90, ge=40, le=100)

    # --- Хранилище и каталог ------------------------------------------------
    data_dir: Path = PROJECT_ROOT / "data"
    catalog_db_path: Path | None = None
    chroma_dir: Path | None = None
    embedding_model: str = "intfloat/multilingual-e5-small"
    match_top_k: int = Field(default=3, ge=1, le=20)
    match_min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)

    # --- Коммерческий расчёт по умолчанию -----------------------------------
    base_currency: str = "ILS"
    default_material_markup_pct: Decimal = Field(default=Decimal("25"), ge=0)
    default_labor_rate_per_hour: Decimal = Field(default=Decimal("180"), ge=0)
    default_contingency_pct: Decimal = Field(default=Decimal("5"), ge=0)
    default_vat_pct: Decimal = Field(default=Decimal("18"), ge=0)
    contractor_name: str = ""

    # --- Приложение ----------------------------------------------------------
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator(
        "model_extractor", "model_validator", "model_matcher", "model_estimator", mode="after"
    )
    @classmethod
    def _non_empty_model(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Идентификатор модели не может быть пустым")
        return v

    @field_validator("base_currency", mode="before")
    @classmethod
    def _currency(cls, v: str) -> str:
        return normalize_currency(v)

    @field_validator("data_dir", "catalog_db_path", "chroma_dir", mode="after")
    @classmethod
    def _absolute(cls, v: Path | None) -> Path | None:
        if v is None:
            return None
        return v if v.is_absolute() else (PROJECT_ROOT / v).resolve()

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper(cls, v: str) -> str:
        return str(v).upper()

    # --- производные пути ----------------------------------------------------

    @property
    def renders_dir(self) -> Path:
        return self.data_dir / "renders"

    @property
    def runs_dir(self) -> Path:
        return self.data_dir / "runs"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def catalog_db(self) -> Path:
        return self.catalog_db_path or (self.data_dir / "catalog.db")

    @property
    def chroma_path(self) -> Path:
        return self.chroma_dir or (self.data_dir / "chroma")

    def ensure_dirs(self) -> None:
        for path in (
            self.data_dir,
            self.renders_dir,
            self.runs_dir,
            self.uploads_dir,
            self.exports_dir,
            self.logs_dir,
            self.chroma_path,
            self.catalog_db.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)

    # --- фабрики -------------------------------------------------------------

    def require_api_key(self) -> str:
        if self.anthropic_api_key is None or not self.anthropic_api_key.get_secret_value().strip():
            raise ConfigurationError(
                "Не задан ANTHROPIC_API_KEY. Скопируйте .env.example в .env и укажите ключ "
                "из консоли Anthropic (platform.claude.com)."
            )
        return self.anthropic_api_key.get_secret_value().strip()

    def pdf_options(self, vision_model_id: str | None = None) -> PdfProcessingOptions:
        """Параметры рендеринга под лимиты Vision модели-экстрактора."""
        profile, _ = get_model_profile(vision_model_id or self.model_extractor)
        side = profile.vision_tile_side_px
        overlap = min(self.pdf_tile_overlap_px, side // 2 - 1)
        return PdfProcessingOptions(
            render_dpi=self.pdf_render_dpi,
            tile_max_edge_px=profile.vision_max_edge_px,
            tile_max_pixels=profile.vision_max_pixels,
            tile_overlap_px=overlap,
            overview_max_edge_px=profile.vision_max_edge_px,
            overview_max_pixels=profile.vision_max_pixels,
            colorspace=self.pdf_colorspace,
            save_full_page=self.pdf_save_full_page,
            full_page_max_megapixels=self.pdf_full_page_max_megapixels,
            extract_tables=self.pdf_extract_tables,
            table_max_vector_paths=self.pdf_table_max_vector_paths,
            jpeg_quality=self.pdf_jpeg_quality,
            max_pages=self.pdf_max_pages,
        )

    def default_estimate_settings(self) -> EstimateSettings:
        return EstimateSettings(
            base_currency=self.base_currency,
            material_markup_pct=self.default_material_markup_pct,
            labor_rate_per_hour=self.default_labor_rate_per_hour,
            contingency_pct=self.default_contingency_pct,
            vat_pct=self.default_vat_pct,
            contractor_name=self.contractor_name,
            terms=CommercialTerms(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Синглтон настроек (читает .env один раз за процесс)."""
    return Settings()


# =============================================================================
# Логирование
# =============================================================================

_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_configured = False


def configure_logging(settings: Settings | None = None) -> None:
    """Консоль + файл ``data/logs/specflow.log`` (5 МБ × 5 файлов, UTF-8)."""
    global _configured
    if _configured:
        return
    settings = settings or get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(settings.log_level)

    # Консоль Windows по умолчанию может быть не в UTF-8.
    stream = sys.stderr
    if hasattr(stream, "reconfigure"):
        # Поток может быть уже обёрнут (IDE, Streamlit) — тогда оставляем как есть.
        with contextlib.suppress(ValueError, OSError):
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    console = logging.StreamHandler(stream)
    console.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt="%H:%M:%S"))

    file_handler = logging.handlers.RotatingFileHandler(
        settings.logs_dir / "specflow.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    root.addHandler(console)
    root.addHandler(file_handler)

    # Шумные библиотеки — только предупреждения.
    for noisy in ("httpx", "httpcore", "chromadb", "urllib3", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True
