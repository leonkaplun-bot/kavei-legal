"""
Этап 0 пайплайна: PDF -> изображения высокого разрешения + текстовый слой + таблицы.

Зачем тайлы
-----------
Лист А3 при 300 DPI — это 4961×3508 px (17 Мп), А1 — 7016×9933 px (70 Мп).
API Claude уменьшает любую картинку до лимита модели (1568 px / ~1,15 Мп для
моделей 4.6; 2576 px / 3,75 Мп для моделей 5.x). Если отправить лист целиком,
шрифт 2,5 мм превратится в 3–4 пикселя и номиналы «C16 / 4,5 кА» станут
нечитаемыми. Поэтому каждая страница отдаётся в двух видах:

* ``overview`` — весь лист, вписанный в лимит модели (композиция, связи, штамп);
* ``tiles`` — сетка фрагментов в полном разрешении 300 DPI, каждый строго
  в лимите модели, с перекрытием ~15 мм, чтобы обозначение на стыке тайлов
  целиком попадало хотя бы в один фрагмент.

Тайлы рендерятся напрямую из векторного PDF через ``clip`` — полный растр
листа в памяти для этого не нужен (А0 при 300 DPI занял бы ~420 МБ).

Дополнительно извлекаются
-------------------------
* текстовый слой (полный текст + слова с координатами, текст внутри каждого
  тайла — Агент 1 получает его как подсказку к изображению);
* таблицы векторного слоя (спецификации, перечни элементов) — в виде строк
  и Markdown;
* метрики содержимого и эвристический тип страницы (чертёж / таблица /
  текст / скан / SHX-текст без текстового слоя);
* формат листа по ГОСТ 2.301 (А4…А0, А4×3 и т.п.).

Результаты кэшируются на диске по SHA-256 файла + отпечатку параметров:
повторная загрузка того же PDF не тратит время на рендеринг.

Запуск для проверки на реальных чертежах (Windows):
    python -m specflow.pdf_processor "D:\\Проекты\\ЩР-1.pdf" --pages 1-3
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import math
import multiprocessing
import re
import time
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf

from specflow.exceptions import (
    PdfEncryptedError,
    PdfOpenError,
    PdfPageSelectionError,
    PdfProcessingError,
    PdfTooManyPagesError,
)
from specflow.schemas import (
    BBox,
    EventLevel,
    ExtractedTable,
    ImageAsset,
    ImageTile,
    PageContentMetrics,
    PageFailure,
    PageKindHint,
    PdfDocumentInfo,
    PdfProcessingOptions,
    PipelineEvent,
    PipelineStage,
    ProcessedDocument,
    ProcessedPage,
    RenderColorspace,
    TextWord,
)

logger = logging.getLogger(__name__)

EventCallback = Callable[[PipelineEvent], None]
PageOutcome = ProcessedPage | PageFailure

PT_PER_INCH = 72.0
MM_PER_PT = 25.4 / 72.0
_TILE_SAFETY_PX = 2  # запас на округление размеров растра в MuPDF
_MAX_TILE_TEXT_CHARS = 4000


def _process_pool(workers: int) -> ProcessPoolExecutor:
    """Пул процессов в режиме spawn — одинаковое поведение на Windows и Linux
    (fork из многопоточного процесса может зависнуть)."""
    return ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn"))

# Не печатать предупреждения MuPDF в stderr — собираем их в warnings страницы.
pymupdf.TOOLS.mupdf_display_errors(False)
pymupdf.TOOLS.mupdf_display_warnings(False)


# =============================================================================
# Чистые функции (геометрия, форматы, выбор страниц)
# =============================================================================

_ISO_A_MM: dict[str, tuple[float, float]] = {
    "A0": (841.0, 1189.0),
    "A1": (594.0, 841.0),
    "A2": (420.0, 594.0),
    "A3": (297.0, 420.0),
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
}


def _close(a: float, b: float, rel: float = 0.02, abs_mm: float = 3.0) -> bool:
    return abs(a - b) <= max(abs_mm, rel * b)


def detect_paper_format(width_pt: float, height_pt: float) -> str:
    """Формат листа: «A3 (альбомный)», «A4x3», «нестандартный 500×700 мм».

    Дополнительные форматы ГОСТ 2.301 (A4x3 = 297×630 мм, A3x3 = 420×891 мм)
    распознаются как кратные коротких сторон основных форматов.
    """
    w_mm, h_mm = width_pt * MM_PER_PT, height_pt * MM_PER_PT
    short, long_ = sorted((w_mm, h_mm))
    orientation = "альбомный" if w_mm > h_mm else "книжный"
    for name, (s, l) in _ISO_A_MM.items():
        if _close(short, s) and _close(long_, l):
            return f"{name} ({orientation})"
    for name, (s, l) in _ISO_A_MM.items():
        if _close(short, l):
            k = round(long_ / s)
            if 2 <= k <= 9 and _close(long_, s * k):
                return f"{name}x{k}"
    return f"нестандартный {round(w_mm)}×{round(h_mm)} мм"


@dataclass(frozen=True)
class TileSpec:
    row: int
    col: int
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def rect(self) -> pymupdf.Rect:
        return pymupdf.Rect(self.x0, self.y0, self.x1, self.y1)

    def bbox(self) -> BBox:
        return BBox(x0=self.x0, y0=self.y0, x1=self.x1, y1=self.y1)


def _axis_starts(length: float, tile: float, overlap: float) -> list[float]:
    """Начала тайлов по оси: равномерно, последний тайл упирается в край листа."""
    if length <= tile:
        return [0.0]
    step = tile - overlap
    n = math.ceil((length - tile) / step) + 1
    actual_step = (length - tile) / (n - 1)
    return [i * actual_step for i in range(n)]


def compute_tile_grid(
    width_pt: float,
    height_pt: float,
    dpi: float,
    tile_px: int,
    overlap_px: int,
) -> list[TileSpec]:
    """Сетка тайлов в координатах страницы (pt).

    Гарантии: тайлы покрывают весь лист; размер тайла в пикселях при ``dpi``
    не превышает ``tile_px``; фактическое перекрытие не меньше ``overlap_px``.
    """
    if tile_px <= 2 * overlap_px:
        raise ValueError("Перекрытие должно быть меньше половины тайла")
    scale = dpi / PT_PER_INCH
    tile_pt = (tile_px - _TILE_SAFETY_PX) / scale
    overlap_pt = overlap_px / scale
    xs = _axis_starts(width_pt, tile_pt, overlap_pt)
    ys = _axis_starts(height_pt, tile_pt, overlap_pt)
    return [
        TileSpec(
            row=r,
            col=c,
            x0=x,
            y0=y,
            x1=min(x + tile_pt, width_pt),
            y1=min(y + tile_pt, height_pt),
        )
        for r, y in enumerate(ys)
        for c, x in enumerate(xs)
    ]


def fit_dpi(width_pt: float, height_pt: float, max_edge_px: int, max_pixels: int, cap_dpi: float) -> float:
    """DPI, при котором весь лист влезает в лимиты по стороне и площади."""
    by_edge = max_edge_px / max(width_pt, height_pt) * PT_PER_INCH
    by_area = math.sqrt(max_pixels / (width_pt * height_pt)) * PT_PER_INCH
    # 1% запаса на округление размеров растра.
    return max(10.0, min(by_edge, by_area, cap_dpi) * 0.99)


_PAGE_SEL_RE = re.compile(r"^\s*(\d+)\s*(?:[-–—]\s*(\d+))?\s*$")


def parse_page_selection(selection: str | Sequence[int] | None, page_count: int) -> list[int]:
    """«1-3, 7, 10-12» -> [1, 2, 3, 7, 10, 11, 12] (нумерация с 1).

    ``None`` — все страницы. Последовательность чисел принимается как есть.
    """
    if page_count <= 0:
        return []
    if selection is None or (isinstance(selection, str) and not selection.strip()):
        return list(range(1, page_count + 1))

    pages: list[int] = []
    if isinstance(selection, str):
        for chunk in re.split(r"[,;]", selection):
            if not chunk.strip():
                continue
            m = _PAGE_SEL_RE.match(chunk)
            if not m:
                raise PdfPageSelectionError(f"Не понимаю выбор страниц: «{chunk.strip()}»")
            start = int(m.group(1))
            end = int(m.group(2) or start)
            if start > end:
                start, end = end, start
            pages.extend(range(start, end + 1))
    else:
        pages = [int(p) for p in selection]

    bad = [p for p in pages if p < 1 or p > page_count]
    if bad:
        raise PdfPageSelectionError(
            f"Страницы {sorted(set(bad))} вне диапазона 1–{page_count}"
        )
    return sorted(set(pages))


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _rows_to_markdown(header: list[str], rows: list[list[str]]) -> str:
    def esc(cell: str) -> str:
        return cell.replace("|", "\\|").replace("\n", " ")

    width = max([len(header)] + [len(r) for r in rows]) if (header or rows) else 0
    if width == 0:
        return ""
    head = (header + [""] * width)[:width] if header else [f"Кол.{i + 1}" for i in range(width)]
    lines = [
        "| " + " | ".join(esc(h) for h in head) + " |",
        "|" + "---|" * width,
    ]
    for r in rows:
        cells = (r + [""] * width)[:width]
        lines.append("| " + " | ".join(esc(c) for c in cells) + " |")
    return "\n".join(lines)


# =============================================================================
# Открытие документа
# =============================================================================


def open_pdf(path: Path, password: str | None = None) -> pymupdf.Document:
    """Открывает PDF с понятными ошибками для пользователя."""
    if not path.exists():
        raise PdfOpenError(f"Файл не найден: {path}")
    if path.stat().st_size == 0:
        raise PdfOpenError(f"Файл пустой: {path.name}")
    try:
        doc = pymupdf.open(path)
    except (pymupdf.FileDataError, pymupdf.EmptyFileError, RuntimeError, ValueError) as exc:
        raise PdfOpenError(f"Не удалось открыть «{path.name}» как PDF: {exc}") from exc
    if not doc.is_pdf:
        doc.close()
        raise PdfOpenError(f"«{path.name}» не является PDF-документом")
    if doc.needs_pass:
        if not password or not doc.authenticate(password):
            doc.close()
            raise PdfEncryptedError(
                f"«{path.name}» защищён паролем. Укажите пароль или загрузите незащищённую копию."
            )
    return doc


def build_document_info(path: Path, doc: pymupdf.Document, sha256: str | None = None) -> PdfDocumentInfo:
    sha = sha256 or file_sha256(path)
    meta = doc.metadata or {}
    return PdfDocumentInfo(
        document_id=sha[:16],
        file_name=path.name,
        file_path=path.resolve(),
        sha256=sha,
        size_bytes=path.stat().st_size,
        page_count=doc.page_count,
        pdf_format=meta.get("format") or "",
        title=meta.get("title") or "",
        author=meta.get("author") or "",
        creator=meta.get("creator") or "",
        producer=meta.get("producer") or "",
        is_encrypted=bool(meta.get("encryption")),
    )


# =============================================================================
# Рендеринг одной страницы
# =============================================================================


class _PageRenderer:
    """Рендерит страницы одного документа. Экземпляр используется из одного потока."""

    def __init__(
        self,
        pdf_path: Path,
        info: PdfDocumentInfo,
        options: PdfProcessingOptions,
        output_dir: Path,
        password: str | None = None,
        use_cache: bool = True,
    ) -> None:
        self.pdf_path = pdf_path
        self.info = info
        self.options = options
        self.output_dir = output_dir
        self.use_cache = use_cache
        self._password = password
        self._doc: pymupdf.Document | None = None

    @property
    def doc(self) -> pymupdf.Document:
        if self._doc is None:
            self._doc = open_pdf(self.pdf_path, self._password)
        return self._doc

    def close(self) -> None:
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    # --- публичный метод ------------------------------------------------------

    def render(self, page_number: int) -> PageOutcome:
        page_dir = self.output_dir / f"page_{page_number:04d}"
        manifest = page_dir / "page.json"

        if self.use_cache:
            cached = self._load_cached(manifest)
            if cached is not None:
                return cached

        started = time.perf_counter()
        pymupdf.TOOLS.reset_mupdf_warnings()
        try:
            page = self.doc.load_page(page_number - 1)
            result = self._render_page(page, page_number, page_dir)
        except Exception as exc:  # noqa: BLE001 — страница не должна валить документ
            logger.exception("Ошибка обработки страницы %s файла %s", page_number, self.info.file_name)
            return PageFailure(
                document_id=self.info.document_id,
                page_number=page_number,
                stage=PipelineStage.PDF_PROCESSING,
                error=f"{type(exc).__name__}: {exc}",
            )

        mupdf_warnings = pymupdf.TOOLS.mupdf_warnings()
        if mupdf_warnings:
            result.warnings.extend(
                f"MuPDF: {w}" for w in mupdf_warnings.splitlines()[:10] if w.strip()
            )
        result.processing_time_s = round(time.perf_counter() - started, 3)

        page_dir.mkdir(parents=True, exist_ok=True)
        manifest.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result

    # --- внутреннее ---------------------------------------------------------

    def _load_cached(self, manifest: Path) -> ProcessedPage | None:
        if not manifest.exists():
            return None
        try:
            page = ProcessedPage.model_validate_json(manifest.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return None
        assets = [page.overview, *(t.image for t in page.tiles)]
        if page.full_page is not None:
            assets.append(page.full_page)
        if all(a.path.exists() for a in assets):
            return page
        return None

    def _colorspace(self) -> pymupdf.Colorspace:
        return pymupdf.csGRAY if self.options.colorspace is RenderColorspace.GRAY else pymupdf.csRGB

    def _pixmap(self, page: pymupdf.Page, dpi: float, clip: pymupdf.Rect | None = None) -> pymupdf.Pixmap:
        """Рендер через матрицу масштаба: параметр dpi= в PyMuPDF принимает только целые."""
        zoom = dpi / PT_PER_INCH
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(zoom, zoom),
            clip=clip,
            colorspace=self._colorspace(),
            alpha=False,
        )
        pix.set_dpi(int(round(dpi)), int(round(dpi)))
        return pix

    def _encode(self, pix: pymupdf.Pixmap) -> tuple[bytes, str, str]:
        """PNG (лучше для линий), JPEG — только если PNG не влезает в лимит."""
        png = pix.tobytes("png")
        if len(png) <= self.options.max_image_bytes:
            return png, "image/png", ".png"
        for quality in sorted({self.options.jpeg_quality, 80, 70, 60}, reverse=True):
            jpg = pix.tobytes("jpg", jpg_quality=quality)
            if len(jpg) <= self.options.max_image_bytes:
                return jpg, "image/jpeg", ".jpg"
        raise PdfProcessingError(
            f"Изображение {pix.width}×{pix.height} не удаётся сжать до "
            f"{self.options.max_image_bytes} байт"
        )

    def _save(self, pix: pymupdf.Pixmap, path_stem: Path, dpi: float) -> ImageAsset:
        data, media_type, ext = self._encode(pix)
        path = path_stem.with_suffix(ext)
        path.write_bytes(data)
        return ImageAsset(
            path=path,
            media_type=media_type,  # type: ignore[arg-type]
            width_px=pix.width,
            height_px=pix.height,
            size_bytes=len(data),
            dpi=round(dpi, 2),
        )

    def _render_clip(self, page: pymupdf.Page, rect: pymupdf.Rect, dpi: float) -> pymupdf.Pixmap:
        """Рендер фрагмента с жёсткой проверкой лимитов Vision."""
        max_edge = self.options.tile_max_edge_px
        max_pixels = self.options.tile_max_pixels
        clip = pymupdf.Rect(rect)
        for _ in range(4):
            pix = self._pixmap(page, dpi, clip)
            if max(pix.width, pix.height) <= max_edge and pix.width * pix.height <= max_pixels:
                return pix
            clip = pymupdf.Rect(clip.x0, clip.y0, clip.x1 - clip.width * 0.005, clip.y1 - clip.height * 0.005)
        return pix

    def _render_page(self, page: pymupdf.Page, page_number: int, page_dir: Path) -> ProcessedPage:
        opts = self.options
        warnings: list[str] = []
        page_dir.mkdir(parents=True, exist_ok=True)

        original_rotation = page.rotation
        if original_rotation:
            # Документ открыт только на чтение, изменение остаётся в памяти.
            # После этого координаты текста совпадают с видимой ориентацией листа.
            page.remove_rotation()

        rect = page.rect
        width_pt, height_pt = rect.width, rect.height
        if width_pt <= 0 or height_pt <= 0:
            raise PdfProcessingError("Нулевой размер страницы")

        # --- текстовый слой ----------------------------------------------------
        text = ""
        words: list[TextWord] = []
        raw_words: list[tuple[Any, ...]] = []
        if opts.extract_text:
            text = page.get_text("text", sort=True) or ""
            raw_words = page.get_text("words", sort=True) or []
            if opts.extract_words:
                words = [
                    TextWord(text=w[4], bbox=BBox(x0=w[0], y0=w[1], x1=w[2], y1=w[3]))
                    for w in raw_words
                    if str(w[4]).strip()
                ]

        # --- метрики ---------------------------------------------------------
        metrics = self._metrics(page, text, raw_words)

        # --- таблицы ---------------------------------------------------------
        tables: list[ExtractedTable] = []
        if opts.extract_tables:
            if metrics.vector_paths <= opts.table_max_vector_paths:
                tables = self._extract_tables(page, page_number, warnings)
            else:
                warnings.append(
                    f"Поиск таблиц пропущен: {metrics.vector_paths} векторных объектов "
                    f"(лимит {opts.table_max_vector_paths})"
                )

        # --- обзор листа -----------------------------------------------------
        ov_dpi = fit_dpi(width_pt, height_pt, opts.overview_max_edge_px, opts.overview_max_pixels, opts.render_dpi)
        ov_pix = self._pixmap(page, ov_dpi)
        overview = self._save(ov_pix, page_dir / "overview", ov_dpi)
        del ov_pix

        # --- полный лист 300 DPI (для UI и аудита) ---------------------------
        full_page: ImageAsset | None = None
        if opts.save_full_page:
            full_dpi = float(opts.render_dpi)
            megapixels = width_pt * height_pt * (full_dpi / PT_PER_INCH) ** 2 / 1e6
            if megapixels > opts.full_page_max_megapixels:
                full_dpi = math.floor(
                    PT_PER_INCH * math.sqrt(opts.full_page_max_megapixels * 1e6 / (width_pt * height_pt))
                )
                warnings.append(
                    f"Полный лист сохранён в {full_dpi} DPI вместо {opts.render_dpi} "
                    f"(лимит {opts.full_page_max_megapixels:g} Мп); тайлы — в {opts.render_dpi} DPI"
                )
            full_pix = self._pixmap(page, full_dpi)
            full_path = (page_dir / f"full_{int(full_dpi)}dpi").with_suffix(".png")
            full_pix.save(full_path)
            full_page = ImageAsset(
                path=full_path,
                media_type="image/png",
                width_px=full_pix.width,
                height_px=full_pix.height,
                size_bytes=full_path.stat().st_size,
                dpi=full_dpi,
            )
            del full_pix

        # --- тайлы 300 DPI ---------------------------------------------------
        tiles: list[ImageTile] = []
        grid = compute_tile_grid(width_pt, height_pt, opts.render_dpi, opts.tile_side_px, opts.tile_overlap_px)
        # Если лист целиком влезает в один тайл, обзор уже в полном разрешении.
        if len(grid) > 1 or ov_dpi < opts.render_dpi * 0.98:
            for spec in grid:
                tile_id = f"p{page_number:03d}_r{spec.row}_c{spec.col}"
                pix = self._render_clip(page, spec.rect, opts.render_dpi)
                asset = self._save(pix, page_dir / tile_id, opts.render_dpi)
                del pix
                tiles.append(
                    ImageTile(
                        tile_id=tile_id,
                        row=spec.row,
                        col=spec.col,
                        bbox_pt=spec.bbox(),
                        image=asset,
                        text_hint=_tile_text(raw_words, spec),
                    )
                )

        return ProcessedPage(
            document_id=self.info.document_id,
            page_number=page_number,
            width_pt=round(width_pt, 3),
            height_pt=round(height_pt, 3),
            original_rotation=original_rotation,
            paper_format=detect_paper_format(width_pt, height_pt),
            render_dpi=opts.render_dpi,
            overview=overview,
            full_page=full_page,
            tiles=tiles,
            text=text,
            words=words,
            tables=tables,
            metrics=metrics,
            kind_hint=_classify(metrics, tables, width_pt * height_pt),
            warnings=warnings,
        )

    def _metrics(self, page: pymupdf.Page, text: str, raw_words: list[tuple[Any, ...]]) -> PageContentMetrics:
        vector_paths = 0
        text_ops = 0
        image_area = 0.0
        raster_images = 0
        page_rect = page.rect
        page_area = max(page_rect.width * page_rect.height, 1.0)
        try:
            for kind, bbox in page.get_bboxlog():
                if kind in ("fill-path", "stroke-path"):
                    vector_paths += 1
                elif kind.endswith("-text"):
                    text_ops += 1
                elif kind in ("fill-image", "fill-imgmask"):
                    raster_images += 1
                    r = pymupdf.Rect(bbox) & page_rect
                    if not r.is_empty:
                        image_area += r.width * r.height
        except Exception as exc:  # noqa: BLE001
            logger.debug("get_bboxlog не сработал: %s", exc)

        char_count = len(text.strip())
        coverage = min(1.0, image_area / page_area)
        likely_scanned = coverage >= 0.8 and char_count < 30
        return PageContentMetrics(
            char_count=char_count,
            word_count=len(raw_words),
            vector_paths=vector_paths,
            text_ops=text_ops,
            raster_images=raster_images,
            raster_coverage=round(coverage, 4),
            likely_scanned=likely_scanned,
            likely_outlined_text=(not likely_scanned and char_count < 30 and vector_paths > 3000),
        )

    def _extract_tables(self, page: pymupdf.Page, page_number: int, warnings: list[str]) -> list[ExtractedTable]:
        try:
            finder = page.find_tables()
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Поиск таблиц завершился ошибкой: {exc}")
            return []

        result: list[ExtractedTable] = []
        for idx, table in enumerate(finder.tables):
            try:
                raw_rows = table.extract()
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Таблица {idx + 1}: ошибка чтения ячеек: {exc}")
                continue
            rows = [[(cell or "").replace("\n", " ").strip() for cell in row] for row in raw_rows]
            total = sum(len(r) for r in rows)
            filled = sum(1 for r in rows for c in r if c)
            # Отсекаем «таблицы» из линий схемы: мало строк/колонок или пустые ячейки.
            if len(rows) < 2 or table.col_count < 2 or total == 0 or filled / total < 0.25:
                continue

            header_obj = getattr(table, "header", None)
            external = bool(getattr(header_obj, "external", False))
            names = [str(n or "").replace("\n", " ").strip() for n in (getattr(header_obj, "names", None) or [])]
            if external:
                header, body = names, rows
            else:
                header, body = rows[0], rows[1:]

            result.append(
                ExtractedTable(
                    table_id=f"p{page_number:03d}_t{idx + 1}",
                    page_number=page_number,
                    bbox_pt=BBox.from_seq(table.bbox),
                    header=header,
                    rows=body,
                    markdown=_rows_to_markdown(header, body),
                )
            )
        return result


def _tile_text(raw_words: list[tuple[Any, ...]], spec: TileSpec) -> str:
    """Текст тайла построчно: слова, центр которых попадает в тайл."""
    if not raw_words:
        return ""
    lines: dict[tuple[int, int], list[str]] = {}
    for w in raw_words:
        x0, y0, x1, y1, word, block_no, line_no = w[0], w[1], w[2], w[3], w[4], w[5], w[6]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if spec.x0 <= cx <= spec.x1 and spec.y0 <= cy <= spec.y1 and str(word).strip():
            lines.setdefault((int(block_no), int(line_no)), []).append(str(word))
    text = "\n".join(" ".join(ws) for ws in lines.values())
    if len(text) > _MAX_TILE_TEXT_CHARS:
        text = text[:_MAX_TILE_TEXT_CHARS] + "\n[…текст тайла обрезан…]"
    return text


def _classify(metrics: PageContentMetrics, tables: list[ExtractedTable], page_area: float) -> PageKindHint:
    if metrics.char_count == 0 and metrics.vector_paths == 0 and metrics.raster_images == 0:
        return PageKindHint.BLANK
    if metrics.likely_scanned:
        return PageKindHint.SCANNED
    table_area = sum(t.bbox_pt.area for t in tables)
    table_rows = sum(t.row_count for t in tables)
    if tables and table_rows >= 3 and table_area / max(page_area, 1.0) >= 0.35:
        return PageKindHint.SPEC_TABLE
    if metrics.vector_paths >= 300 or metrics.likely_outlined_text:
        return PageKindHint.DRAWING
    if metrics.char_count >= 800:
        return PageKindHint.TEXT_DOCUMENT
    return PageKindHint.MIXED


# =============================================================================
# Работа в отдельном процессе (PDF_WORKERS > 0)
# =============================================================================


@dataclass(frozen=True)
class _Prepared:
    path: Path
    info: PdfDocumentInfo
    selected: list[int]
    out_dir: Path


@dataclass(frozen=True)
class _PageJob:
    pdf_path: Path
    info: PdfDocumentInfo
    options: PdfProcessingOptions
    output_dir: Path
    page_number: int
    password: str | None
    use_cache: bool


def _render_page_job(job: _PageJob) -> PageOutcome:
    """Точка входа для ProcessPoolExecutor (функция уровня модуля — требование spawn на Windows)."""
    renderer = _PageRenderer(job.pdf_path, job.info, job.options, job.output_dir, job.password, job.use_cache)
    try:
        return renderer.render(job.page_number)
    except PdfProcessingError as exc:
        return PageFailure(
            document_id=job.info.document_id,
            page_number=job.page_number,
            stage=PipelineStage.PDF_PROCESSING,
            error=str(exc),
        )
    finally:
        renderer.close()


# =============================================================================
# Публичный API
# =============================================================================


class PdfProcessor:
    """Обработка PDF-документов для пайплайна SpecFlow AI.

    Пример::

        processor = PdfProcessor(settings.pdf_options(), settings.renders_dir)
        doc = processor.process(Path("ЩР-1.pdf"), pages="1-4")
        for page in doc.pages:
            print(page.page_number, page.kind_hint, len(page.tiles))

    Асинхронно (страницы отдаются по мере готовности — Агент 1 может
    начинать работу с первой страницей, пока рендерятся следующие)::

        async for outcome in processor.aiter_pages(path):
            if isinstance(outcome, ProcessedPage):
                await extractor.extract_page(outcome)

    PyMuPDF не потокобезопасен, поэтому в режиме ``workers=0`` все обращения
    к документу идут из одного выделенного потока, а при ``workers>0`` —
    из отдельных процессов (каждый открывает файл сам).
    """

    def __init__(
        self,
        options: PdfProcessingOptions | None = None,
        output_root: Path | None = None,
        *,
        workers: int = 0,
        use_cache: bool = True,
    ) -> None:
        self.options = options or PdfProcessingOptions()
        self.output_root = Path(output_root) if output_root else Path.cwd() / "data" / "renders"
        self.workers = max(0, workers)
        self.use_cache = use_cache

    # --- подготовка -----------------------------------------------------------

    def inspect(self, pdf_path: Path | str, password: str | None = None) -> PdfDocumentInfo:
        """Метаданные документа без рендеринга (для UI: число страниц, размер)."""
        path = Path(pdf_path)
        doc = open_pdf(path, password)
        try:
            return build_document_info(path, doc)
        finally:
            doc.close()

    def _prepare(
        self,
        pdf_path: Path | str,
        pages: str | Sequence[int] | None,
        password: str | None,
    ) -> _Prepared:
        path = Path(pdf_path)
        info = self.inspect(path, password)
        selected = parse_page_selection(pages, info.page_count)
        if not selected:
            raise PdfProcessingError(f"В документе «{path.name}» нет страниц")
        if len(selected) > self.options.max_pages:
            raise PdfTooManyPagesError(
                f"Выбрано {len(selected)} стр., лимит — {self.options.max_pages} "
                f"(PDF_MAX_PAGES). Укажите диапазон страниц, например «1-{self.options.max_pages}»."
            )
        out_dir = self.output_root / f"{info.document_id}_{self.options.fingerprint()}"
        out_dir.mkdir(parents=True, exist_ok=True)
        return _Prepared(path=path, info=info, selected=selected, out_dir=out_dir)

    @staticmethod
    def _emit(on_event: EventCallback | None, event: PipelineEvent) -> None:
        if on_event is None:
            return
        try:
            on_event(event)
        except Exception:  # noqa: BLE001 — сбой UI-колбэка не должен ронять обработку
            logger.warning("Ошибка в обработчике события", exc_info=True)

    def _progress_event(self, info: PdfDocumentInfo, outcome: PageOutcome, done: int, total: int) -> PipelineEvent:
        if isinstance(outcome, PageFailure):
            return PipelineEvent(
                stage=PipelineStage.PDF_PROCESSING,
                level=EventLevel.ERROR,
                message=f"{info.file_name}: стр. {outcome.page_number} — ошибка: {outcome.error}",
                progress=done / total,
                details={"document_id": info.document_id, "page": outcome.page_number},
            )
        return PipelineEvent(
            stage=PipelineStage.PDF_PROCESSING,
            level=EventLevel.WARNING if outcome.warnings else EventLevel.INFO,
            message=(
                f"{info.file_name}: стр. {outcome.page_number}/{info.page_count} · "
                f"{outcome.paper_format} · {outcome.kind_hint.value} · "
                f"тайлов {len(outcome.tiles)} · таблиц {len(outcome.tables)}"
            ),
            progress=done / total,
            details={
                "document_id": info.document_id,
                "page": outcome.page_number,
                "tiles": len(outcome.tiles),
                "tables": len(outcome.tables),
                "estimated_image_tokens": outcome.estimated_image_tokens,
                "warnings": outcome.warnings,
            },
        )

    def _start_event(self, info: PdfDocumentInfo, selected: list[int]) -> PipelineEvent:
        return PipelineEvent(
            stage=PipelineStage.PDF_PROCESSING,
            level=EventLevel.INFO,
            message=f"{info.file_name}: {len(selected)} из {info.page_count} стр., рендеринг {self.options.render_dpi} DPI",
            progress=0.0,
            details={"document_id": info.document_id, "pages": selected},
        )

    # --- синхронный режим -----------------------------------------------------

    def iter_pages(
        self,
        pdf_path: Path | str,
        pages: str | Sequence[int] | None = None,
        password: str | None = None,
        on_event: EventCallback | None = None,
    ) -> Iterator[PageOutcome]:
        """Генератор результатов по страницам (в порядке номеров)."""
        prepared = self._prepare(pdf_path, pages, password)
        yield from self._iter_prepared(prepared, password, on_event)

    def _iter_prepared(
        self,
        prep: _Prepared,
        password: str | None,
        on_event: EventCallback | None,
    ) -> Iterator[PageOutcome]:
        self._emit(on_event, self._start_event(prep.info, prep.selected))
        total = len(prep.selected)

        if self.workers > 0 and total > 1:
            jobs = [
                _PageJob(prep.path, prep.info, self.options, prep.out_dir, n, password, self.use_cache)
                for n in prep.selected
            ]
            with _process_pool(min(self.workers, total)) as pool:
                for done, outcome in enumerate(pool.map(_render_page_job, jobs), start=1):
                    self._emit(on_event, self._progress_event(prep.info, outcome, done, total))
                    yield outcome
            return

        renderer = _PageRenderer(prep.path, prep.info, self.options, prep.out_dir, password, self.use_cache)
        try:
            for done, n in enumerate(prep.selected, start=1):
                outcome = renderer.render(n)
                self._emit(on_event, self._progress_event(prep.info, outcome, done, total))
                yield outcome
        finally:
            renderer.close()

    def process(
        self,
        pdf_path: Path | str,
        pages: str | Sequence[int] | None = None,
        password: str | None = None,
        on_event: EventCallback | None = None,
    ) -> ProcessedDocument:
        """Обработать документ целиком и сохранить манифест ``document.json``."""
        prep = self._prepare(pdf_path, pages, password)
        processed: list[ProcessedPage] = []
        failures: list[PageFailure] = []
        for outcome in self._iter_prepared(prep, password, on_event):
            if isinstance(outcome, PageFailure):
                failures.append(outcome)
            else:
                processed.append(outcome)
        return self._finalize(prep, processed, failures, on_event)

    def _finalize(
        self,
        prep: _Prepared,
        processed: list[ProcessedPage],
        failures: list[PageFailure],
        on_event: EventCallback | None,
    ) -> ProcessedDocument:
        document = ProcessedDocument(
            info=prep.info,
            options=self.options,
            output_dir=prep.out_dir,
            pages=sorted(processed, key=lambda p: p.page_number),
            failures=failures,
        )
        # Слова с координатами уже лежат в page.json каждой страницы.
        (prep.out_dir / "document.json").write_text(
            document.model_dump_json(indent=2, exclude={"pages": {"__all__": {"words"}}}),
            encoding="utf-8",
        )
        level = EventLevel.SUCCESS if not failures else EventLevel.WARNING
        tokens = f"{document.estimated_image_tokens:,}".replace(",", " ")
        self._emit(
            on_event,
            PipelineEvent(
                stage=PipelineStage.PDF_PROCESSING,
                level=level,
                message=(
                    f"{prep.info.file_name}: готово {len(processed)} стр., ошибок {len(failures)}, "
                    f"≈{tokens} токенов изображений"
                ),
                progress=1.0,
                details={"document_id": prep.info.document_id, "output_dir": str(prep.out_dir)},
            ),
        )
        return document

    # --- асинхронный режим ----------------------------------------------------

    async def aiter_pages(
        self,
        pdf_path: Path | str,
        pages: str | Sequence[int] | None = None,
        password: str | None = None,
        on_event: EventCallback | None = None,
    ) -> AsyncIterator[PageOutcome]:
        """Асинхронный генератор: CPU-работа вынесена из event loop."""
        prep = await asyncio.to_thread(self._prepare, pdf_path, pages, password)
        async for outcome in self._aiter_prepared(prep, password, on_event):
            yield outcome

    async def _aiter_prepared(
        self,
        prep: _Prepared,
        password: str | None,
        on_event: EventCallback | None,
    ) -> AsyncIterator[PageOutcome]:
        loop = asyncio.get_running_loop()
        self._emit(on_event, self._start_event(prep.info, prep.selected))
        total = len(prep.selected)

        if self.workers > 0 and total > 1:
            pool = _process_pool(min(self.workers, total))
            try:
                futures = [
                    loop.run_in_executor(
                        pool,
                        _render_page_job,
                        _PageJob(prep.path, prep.info, self.options, prep.out_dir, n, password, self.use_cache),
                    )
                    for n in prep.selected
                ]
                for done, fut in enumerate(futures, start=1):
                    outcome = await fut
                    self._emit(on_event, self._progress_event(prep.info, outcome, done, total))
                    yield outcome
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
            return

        # Один выделенный поток: PyMuPDF не потокобезопасен.
        thread = ThreadPoolExecutor(max_workers=1, thread_name_prefix="specflow-pdf")
        renderer = _PageRenderer(prep.path, prep.info, self.options, prep.out_dir, password, self.use_cache)
        try:
            for done, n in enumerate(prep.selected, start=1):
                outcome = await loop.run_in_executor(thread, renderer.render, n)
                self._emit(on_event, self._progress_event(prep.info, outcome, done, total))
                yield outcome
        finally:
            await loop.run_in_executor(thread, renderer.close)
            thread.shutdown(wait=True)

    async def process_async(
        self,
        pdf_path: Path | str,
        pages: str | Sequence[int] | None = None,
        password: str | None = None,
        on_event: EventCallback | None = None,
    ) -> ProcessedDocument:
        prep = await asyncio.to_thread(self._prepare, pdf_path, pages, password)
        processed: list[ProcessedPage] = []
        failures: list[PageFailure] = []
        async for outcome in self._aiter_prepared(prep, password, on_event):
            if isinstance(outcome, PageFailure):
                failures.append(outcome)
            else:
                processed.append(outcome)
        return await asyncio.to_thread(self._finalize, prep, processed, failures, on_event)


# =============================================================================
# CLI для ручной проверки на реальных чертежах
# =============================================================================


def _cli(argv: Sequence[str] | None = None) -> int:
    from specflow.config import configure_logging, estimate_image_input_cost, get_settings

    parser = argparse.ArgumentParser(
        prog="python -m specflow.pdf_processor",
        description="Рендеринг PDF-чертежей для SpecFlow AI и оценка стоимости Vision-анализа.",
    )
    parser.add_argument("pdf", type=Path, help="Путь к PDF")
    parser.add_argument("--pages", default=None, help="Страницы: «1-3,7». По умолчанию все.")
    parser.add_argument("--password", default=None, help="Пароль PDF, если защищён")
    parser.add_argument("--model", default=None, help="Модель-экстрактор для лимитов тайлов и оценки цены")
    parser.add_argument("--no-cache", action="store_true", help="Игнорировать кэш рендеринга")
    args = parser.parse_args(argv)

    settings = get_settings()
    configure_logging(settings)
    settings.ensure_dirs()
    model = args.model or settings.model_extractor

    processor = PdfProcessor(
        settings.pdf_options(model),
        settings.renders_dir,
        workers=settings.pdf_workers,
        use_cache=not args.no_cache,
    )

    def printer(event: PipelineEvent) -> None:
        pct = f"{event.progress * 100:5.1f}%" if event.progress is not None else "      "
        print(f"[{pct}] {event.level.value.upper():7} {event.message}")

    try:
        document = processor.process(args.pdf, pages=args.pages, password=args.password, on_event=printer)
    except PdfProcessingError as exc:
        print(f"ОШИБКА: {exc}")
        return 2

    print("\nСтр. | Формат            | Тип            | Тайлов | Таблиц | Символов | ≈Токенов")
    print("-----+-------------------+----------------+--------+--------+----------+---------")
    for p in document.pages:
        print(
            f"{p.page_number:>4} | {p.paper_format[:17]:<17} | {p.kind_hint.value:<14} | "
            f"{len(p.tiles):>6} | {len(p.tables):>6} | {p.metrics.char_count:>8} | {p.estimated_image_tokens:>8}"
        )
        for w in p.warnings:
            print(f"     ⚠ {w}")
    for f in document.failures:
        print(f"{f.page_number:>4} | ОШИБКА: {f.error}")

    tokens = document.estimated_image_tokens
    cost = estimate_image_input_cost(tokens, model)
    tokens_fmt = f"{tokens:,}".replace(",", " ")
    print(
        f"\nИтого ≈{tokens_fmt} входных токенов изображений → ≈${cost:.2f} на {model} "
        f"(только картинки, без промпта и ответа)"
    )
    print(f"Файлы: {document.output_dir}")
    summary = {
        "document_id": document.info.document_id,
        "pages": len(document.pages),
        "failures": len(document.failures),
        "estimated_image_tokens": tokens,
        "estimated_image_cost_usd": str(cost),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not document.failures else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
