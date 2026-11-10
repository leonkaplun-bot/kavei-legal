from __future__ import annotations

import asyncio
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from specflow.exceptions import (
    PdfEncryptedError,
    PdfOpenError,
    PdfPageSelectionError,
    PdfTooManyPagesError,
)
from specflow.pdf_processor import (
    PdfProcessor,
    _PageRenderer,
    compute_tile_grid,
    detect_paper_format,
    fit_dpi,
    parse_page_selection,
)
from specflow.normalization import expand_designations
from specflow.schemas import (
    PageKindHint,
    PdfProcessingOptions,
    PipelineEvent,
    ProcessedPage,
    RenderColorspace,
)

# --- чистые функции -----------------------------------------------------------


@pytest.mark.parametrize(
    ("w_pt", "h_pt", "dpi", "tile", "overlap"),
    [
        (1190.55, 841.89, 300, 1072, 180),   # A3 альбом, модели 4.6
        (1683.78, 2383.94, 300, 1936, 180),  # A1, модели 5.x
        (595.28, 841.89, 300, 1072, 0),      # A4 без перекрытия
        (200.0, 150.0, 300, 1072, 180),      # лист меньше тайла
    ],
)
def test_tile_grid_covers_page_within_limits(w_pt, h_pt, dpi, tile, overlap):
    tiles = compute_tile_grid(w_pt, h_pt, dpi, tile, overlap)
    scale = dpi / 72
    # каждый тайл не больше лимита в пикселях
    for t in tiles:
        assert (t.x1 - t.x0) * scale <= tile
        assert (t.y1 - t.y0) * scale <= tile
        assert t.x0 >= 0 and t.y0 >= 0 and t.x1 <= w_pt + 1e-6 and t.y1 <= h_pt + 1e-6
    # покрытие: последний тайл упирается в край
    assert max(t.x1 for t in tiles) == pytest.approx(w_pt)
    assert max(t.y1 for t in tiles) == pytest.approx(h_pt)
    # фактическое перекрытие соседних тайлов не меньше заданного
    cols = sorted({t.x0 for t in tiles})
    tile_pt = (tile - 2) / scale
    for a, b in zip(cols, cols[1:]):
        assert (a + tile_pt - b) * scale >= overlap - 1e-6


def test_tile_grid_rejects_huge_overlap():
    with pytest.raises(ValueError):
        compute_tile_grid(1000, 1000, 300, 400, 200)


@pytest.mark.parametrize(
    ("w_pt", "h_pt", "expected"),
    [
        (1190.55, 841.89, "A3 (альбомный)"),
        (595.28, 841.89, "A4 (книжный)"),
        (2383.94, 3370.39, "A0 (книжный)"),
        (297 / 25.4 * 72, 630 / 25.4 * 72, "A4x3"),
        (420 / 25.4 * 72, 891 / 25.4 * 72, "A3x3"),
    ],
)
def test_detect_paper_format(w_pt, h_pt, expected):
    assert detect_paper_format(w_pt, h_pt) == expected


def test_detect_paper_format_custom():
    assert detect_paper_format(500 / 25.4 * 72, 700 / 25.4 * 72).startswith("нестандартный 500×700")


def test_parse_page_selection():
    assert parse_page_selection(None, 5) == [1, 2, 3, 4, 5]
    assert parse_page_selection("1-3, 5", 5) == [1, 2, 3, 5]
    assert parse_page_selection("3-1;2", 5) == [1, 2, 3]
    assert parse_page_selection([4, 2, 2], 5) == [2, 4]
    with pytest.raises(PdfPageSelectionError):
        parse_page_selection("1-9", 5)
    with pytest.raises(PdfPageSelectionError):
        parse_page_selection("abc", 5)


def test_fit_dpi_respects_limits():
    dpi = fit_dpi(1190.55, 841.89, 1568, 1_150_000, 300)
    w = 1190.55 * dpi / 72
    h = 841.89 * dpi / 72
    assert max(w, h) <= 1568
    assert w * h <= 1_150_000


# --- полный цикл обработки ----------------------------------------------------


def _png_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as im:
        return im.size


def test_process_project_pdf(project_pdf: Path, tmp_path: Path, legacy_options: PdfProcessingOptions):
    events: list[PipelineEvent] = []
    processor = PdfProcessor(legacy_options, tmp_path / "renders")
    doc = processor.process(project_pdf, on_event=events.append)

    assert doc.info.page_count == 4
    assert len(doc.pages) == 4
    assert not doc.failures
    assert (doc.output_dir / "document.json").exists()

    p1, p2, p3, p4 = doc.pages

    # Лист 1: A3-схема
    assert p1.paper_format == "A3 (альбомный)"
    assert p1.kind_hint is PageKindHint.DRAWING
    assert p1.metrics.vector_paths >= 300
    assert "QF1" in p1.text and "Ввод 1" in p1.text
    # 4961×3508 px, тайл 1070 px, перекрытие ≥180 px -> сетка 6×4
    assert len(p1.tiles) == 24
    assert {t.row for t in p1.tiles} == {0, 1, 2, 3}
    assert {t.col for t in p1.tiles} == {0, 1, 2, 3, 4, 5}
    side = legacy_options.tile_side_px
    for tile in p1.tiles:
        w, h = _png_size(tile.image.path)
        assert (w, h) == (tile.image.width_px, tile.image.height_px)
        assert max(w, h) <= legacy_options.tile_max_edge_px
        assert w * h <= legacy_options.tile_max_pixels
        assert w <= side and h <= side
    ow, oh = _png_size(p1.overview.path)
    assert max(ow, oh) <= 1568 and ow * oh <= 1_150_000
    assert p1.full_page is not None
    assert (p1.full_page.width_px, p1.full_page.height_px) == (4961, 3508)

    # подсказка текстового слоя попала в правильный тайл
    hinted = [t for t in p1.tiles if "QF1" in t.text_hint.split()]
    assert hinted, "обозначение QF1 должно попасть в тайл"
    assert {(t.row, t.col) for t in hinted} == {(0, 0)}

    # таблица перечня элементов
    assert len(p1.tables) == 1
    table = p1.tables[0]
    assert table.header == ["Поз.", "Наименование", "Кол.", "Прим."]
    # шрифт может подменить «…» на «⋯» — нормализация обязана это переварить
    assert expand_designations(table.rows[0][0]) == [f"QF{i}" for i in range(1, 7)]
    assert table.rows[2][2] == "24"
    assert "| Поз. |" in table.markdown

    # Лист 2: текст ТЗ
    assert p2.kind_hint is PageKindHint.TEXT_DOCUMENT
    assert "щита управления насосной" in p2.text

    # Лист 3: повёрнутый
    assert p3.original_rotation == 90
    assert p3.width_pt > p3.height_pt  # после снятия поворота лист альбомный
    assert "LC1D09" in p3.text
    for w in p3.words:
        assert 0 <= w.bbox.x0 <= p3.width_pt and 0 <= w.bbox.y0 <= p3.height_pt
    assert any("LC1D09" in t.text_hint for t in p3.tiles)

    # Лист 4: пустой
    assert p4.kind_hint is PageKindHint.BLANK

    # события прогресса
    assert events[0].progress == 0.0
    assert events[-1].progress == 1.0
    progresses = [e.progress for e in events if e.progress is not None]
    assert progresses == sorted(progresses)

    # манифест страницы валиден
    manifest = doc.output_dir / "page_0001" / "page.json"
    reloaded = ProcessedPage.model_validate_json(manifest.read_text(encoding="utf-8"))
    assert reloaded.tiles[0].tile_id == p1.tiles[0].tile_id


def test_cache_skips_rendering(project_pdf: Path, tmp_path: Path, legacy_options, monkeypatch):
    processor = PdfProcessor(legacy_options, tmp_path / "renders")
    first = processor.process(project_pdf, pages="1")

    def boom(*args, **kwargs):
        raise AssertionError("рендеринг не должен вызываться при попадании в кэш")

    monkeypatch.setattr(_PageRenderer, "_render_page", boom)
    second = processor.process(project_pdf, pages="1")
    assert second.pages[0].tiles[0].image.path == first.pages[0].tiles[0].image.path

    # без кэша — рендер вызывается и ошибка страницы не валит документ
    nocache = PdfProcessor(legacy_options, tmp_path / "renders", use_cache=False)
    result = nocache.process(project_pdf, pages="1")
    assert not result.pages and len(result.failures) == 1
    assert "AssertionError" in result.failures[0].error


def test_page_selection_and_limit(project_pdf: Path, tmp_path: Path, legacy_options):
    processor = PdfProcessor(legacy_options, tmp_path / "r")
    doc = processor.process(project_pdf, pages="2,4")
    assert [p.page_number for p in doc.pages] == [2, 4]

    limited = PdfProcessor(legacy_options.model_copy(update={"max_pages": 2}), tmp_path / "r")
    with pytest.raises(PdfTooManyPagesError):
        limited.process(project_pdf)


def test_scanned_page_detected(scanned_pdf: Path, tmp_path: Path, legacy_options):
    doc = PdfProcessor(legacy_options, tmp_path / "r").process(scanned_pdf)
    page = doc.pages[0]
    assert page.kind_hint is PageKindHint.SCANNED
    assert page.metrics.likely_scanned
    assert page.metrics.raster_coverage > 0.95
    assert not page.metrics.has_text_layer


def test_encrypted_pdf(encrypted_pdf: Path, tmp_path: Path, legacy_options):
    processor = PdfProcessor(legacy_options, tmp_path / "r")
    with pytest.raises(PdfEncryptedError):
        processor.process(encrypted_pdf)
    with pytest.raises(PdfEncryptedError):
        processor.process(encrypted_pdf, password="wrong")
    doc = processor.process(encrypted_pdf, password="user-pass")
    assert "secret" in doc.pages[0].text


def test_not_a_pdf(tmp_path: Path, legacy_options):
    bad = tmp_path / "fake.pdf"
    bad.write_text("это не pdf", encoding="utf-8")
    with pytest.raises(PdfOpenError):
        PdfProcessor(legacy_options, tmp_path / "r").process(bad)
    empty = tmp_path / "empty.pdf"
    empty.write_bytes(b"")
    with pytest.raises(PdfOpenError):
        PdfProcessor(legacy_options, tmp_path / "r").process(empty)
    with pytest.raises(PdfOpenError):
        PdfProcessor(legacy_options, tmp_path / "r").process(tmp_path / "missing.pdf")


def test_grayscale_and_no_full_page(project_pdf: Path, tmp_path: Path, legacy_options):
    opts = legacy_options.model_copy(update={"colorspace": RenderColorspace.GRAY, "save_full_page": False})
    doc = PdfProcessor(opts, tmp_path / "r").process(project_pdf, pages="1")
    page = doc.pages[0]
    assert page.full_page is None
    with Image.open(page.tiles[0].image.path) as im:
        assert im.mode == "L"


def test_full_page_megapixel_cap(project_pdf: Path, tmp_path: Path, legacy_options):
    opts = legacy_options.model_copy(update={"full_page_max_megapixels": 4.0})
    page = PdfProcessor(opts, tmp_path / "r").process(project_pdf, pages="1").pages[0]
    assert page.full_page is not None
    assert page.full_page.width_px * page.full_page.height_px <= 4_000_000
    assert any("DPI вместо" in w for w in page.warnings)
    # тайлы при этом остаются в 300 DPI
    assert page.tiles[0].image.dpi == 300


def test_high_res_model_options_produce_fewer_tiles(project_pdf: Path, tmp_path: Path):
    opts = PdfProcessingOptions(
        tile_max_edge_px=2576,
        tile_max_pixels=3_750_000,
        overview_max_edge_px=2576,
        overview_max_pixels=3_750_000,
        save_full_page=False,
    )
    page = PdfProcessor(opts, tmp_path / "r").process(project_pdf, pages="1").pages[0]
    assert opts.tile_side_px == 1936
    assert len(page.tiles) == 6  # сетка 3×2 вместо 6×4 у моделей 4.6
    for t in page.tiles:
        assert t.image.width_px <= 1936 and t.image.height_px <= 1936


def test_jpeg_fallback_when_png_too_large(tmp_path: Path, legacy_options):
    import random

    rng = random.Random(7)
    samples = bytearray(rng.getrandbits(8) for _ in range(600 * 600 * 3))
    pix = pymupdf.Pixmap(pymupdf.csRGB, 600, 600, bytes(samples), False)
    renderer = _PageRenderer.__new__(_PageRenderer)
    renderer.options = legacy_options.model_copy(update={"max_image_bytes": 700_000})
    data, media_type, ext = renderer._encode(pix)
    assert media_type == "image/jpeg" and ext == ".jpg"
    assert len(data) <= 700_000


def test_async_processing_matches_sync(project_pdf: Path, tmp_path: Path, legacy_options):
    processor = PdfProcessor(legacy_options, tmp_path / "async")
    events: list[PipelineEvent] = []
    doc = asyncio.run(processor.process_async(project_pdf, pages="1-3", on_event=events.append))
    assert [p.page_number for p in doc.pages] == [1, 2, 3]
    assert events[-1].progress == 1.0

    async def collect() -> list[int]:
        return [o.page_number async for o in processor.aiter_pages(project_pdf, pages="2-3")]

    assert asyncio.run(collect()) == [2, 3]


def test_process_pool_workers(project_pdf: Path, tmp_path: Path, legacy_options):
    processor = PdfProcessor(legacy_options, tmp_path / "pool", workers=2, use_cache=False)
    doc = processor.process(project_pdf)
    assert [p.page_number for p in doc.pages] == [1, 2, 3, 4]
    assert not doc.failures
    async_doc = asyncio.run(processor.process_async(project_pdf, pages="1-2"))
    assert [p.page_number for p in async_doc.pages] == [1, 2]
