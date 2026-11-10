"""Фикстуры: синтетические PDF, имитирующие реальные проектные документы."""

from __future__ import annotations

import random
from pathlib import Path

import pymupdf
import pytest

from specflow.schemas import PdfProcessingOptions

A3_LANDSCAPE = (1190.55, 841.89)
A4_PORTRAIT = (595.28, 841.89)
CYR_FONT = "china-s"  # встроенный в PyMuPDF шрифт с кириллицей


def _draw_schematic(page: pymupdf.Page) -> None:
    """Имитация однолинейной схемы: шина, отходящие линии, УГО, подписи."""
    rng = random.Random(42)
    page.draw_line((60, 120), (1100, 120), width=2)  # шина
    for i in range(12):
        x = 90 + i * 85
        page.draw_line((x, 120), (x, 600), width=0.8)
        page.draw_rect(pymupdf.Rect(x - 12, 200, x + 12, 240), width=0.8)  # автомат
        page.insert_text((x - 20, 195), f"QF{i + 1}", fontsize=7, fontname=CYR_FONT)
        page.insert_text((x - 20, 255), "C16 3P", fontsize=6, fontname=CYR_FONT)
        # «шум» мелких элементов, как на реальной схеме
        for _ in range(25):
            y = rng.uniform(260, 590)
            page.draw_line((x - 6, y), (x + 6, y + rng.uniform(-3, 3)), width=0.3)
    page.insert_text((60, 100), "Ввод 1: QS1 ВН-32 3P 63А", fontsize=8, fontname=CYR_FONT)


def _draw_table(page: pymupdf.Page, x0: float, y0: float, rows: list[list[str]], widths: list[float]) -> None:
    row_h = 18
    total_w = sum(widths)
    for i in range(len(rows) + 1):
        page.draw_line((x0, y0 + i * row_h), (x0 + total_w, y0 + i * row_h), width=0.6)
    x = x0
    for w in [0.0, *widths]:
        x += w
        page.draw_line((x, y0), (x, y0 + len(rows) * row_h), width=0.6)
    for r, row in enumerate(rows):
        cx = x0
        for c, cell in enumerate(row):
            page.insert_text((cx + 3, y0 + r * row_h + 13), cell, fontsize=7, fontname=CYR_FONT)
            cx += widths[c]


SPEC_ROWS = [
    ["Поз.", "Наименование", "Кол.", "Прим."],
    ["QF1…QF6", "Выключатель автоматический C16 3P 4,5кА", "6", ""],
    ["KM1", "Контактор 25А катушка 230В AC", "1", ""],
    ["XT1", "Клемма проходная 2,5 мм²", "24", ""],
]


def build_project_pdf(path: Path) -> Path:
    doc = pymupdf.open()

    # 1. Схема А3 + небольшая таблица перечня элементов в углу
    p1 = doc.new_page(width=A3_LANDSCAPE[0], height=A3_LANDSCAPE[1])
    _draw_schematic(p1)
    _draw_table(p1, 700, 650, SPEC_ROWS, [55, 230, 35, 50])
    p1.insert_text((900, 820), "Шифр 12-24-ЭМ  Лист 1", fontsize=8, fontname=CYR_FONT)

    # 2. Текстовое ТЗ А4
    p2 = doc.new_page(width=A4_PORTRAIT[0], height=A4_PORTRAIT[1])
    para = (
        "Техническое задание на изготовление щита управления насосной станцией. "
        "Ввод 3Ф 400В 50Гц, IP54, климатическое исполнение УХЛ4. "
    )
    y = 60.0
    for i in range(40):
        p2.insert_text((50, y), f"{i + 1}. {para[: 80]}", fontsize=8, fontname=CYR_FONT)
        y += 18

    # 3. Повёрнутый лист (как бывает у сканов/экспортов САПР)
    p3 = doc.new_page(width=A4_PORTRAIT[0], height=A4_PORTRAIT[1])
    p3.insert_text((60, 80), "ROTATED KM2 LC1D09", fontsize=14)
    p3.set_rotation(90)

    # 4. Пустой лист
    doc.new_page(width=A4_PORTRAIT[0], height=A4_PORTRAIT[1])

    doc.save(path)
    doc.close()
    return path


@pytest.fixture()
def project_pdf(tmp_path: Path) -> Path:
    return build_project_pdf(tmp_path / "project.pdf")


@pytest.fixture()
def scanned_pdf(tmp_path: Path) -> Path:
    """Скан: страница целиком — растровая картинка, текстового слоя нет."""
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 400, 560), False)
    pix.clear_with(235)
    rng = random.Random(1)
    for _ in range(3000):
        pix.set_pixel(rng.randrange(400), rng.randrange(560), (20, 20, 20))
    doc = pymupdf.open()
    page = doc.new_page(width=A4_PORTRAIT[0], height=A4_PORTRAIT[1])
    page.insert_image(page.rect, pixmap=pix)
    path = tmp_path / "scan.pdf"
    doc.save(path)
    doc.close()
    return path


@pytest.fixture()
def encrypted_pdf(tmp_path: Path) -> Path:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "secret QF1", fontsize=12)
    path = tmp_path / "locked.pdf"
    doc.save(
        path,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner-pass",
        user_pw="user-pass",
        permissions=pymupdf.PDF_PERM_PRINT,
    )
    doc.close()
    return path


@pytest.fixture()
def legacy_options() -> PdfProcessingOptions:
    """Лимиты Vision моделей 4.6: 1568 px / 1,15 Мп -> тайл 1072 px."""
    return PdfProcessingOptions(
        render_dpi=300,
        tile_max_edge_px=1568,
        tile_max_pixels=1_150_000,
        tile_overlap_px=180,
        overview_max_edge_px=1568,
        overview_max_pixels=1_150_000,
    )
