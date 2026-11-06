"""Иерархия исключений SpecFlow AI.

Каждое исключение несёт сообщение, пригодное для показа пользователю в UI
(на русском), — технические детали пишутся в лог отдельно.
"""

from __future__ import annotations


class SpecFlowError(Exception):
    """Базовое исключение платформы."""


class ConfigurationError(SpecFlowError):
    """Неверная или неполная конфигурация (.env, ключ API, пути)."""


class PdfProcessingError(SpecFlowError):
    """Ошибка этапа обработки PDF."""


class PdfOpenError(PdfProcessingError):
    """Файл не открывается как PDF (повреждён, пустой, другой формат)."""


class PdfEncryptedError(PdfProcessingError):
    """PDF защищён паролем, а пароль не передан или неверен."""


class PdfTooManyPagesError(PdfProcessingError):
    """Выбрано больше страниц, чем разрешено лимитом PDF_MAX_PAGES."""


class PdfPageSelectionError(PdfProcessingError):
    """Некорректная строка выбора страниц («1-3,7»)."""


class PdfPageError(PdfProcessingError):
    """Ошибка обработки конкретной страницы."""

    def __init__(self, page_number: int, message: str) -> None:
        super().__init__(f"Страница {page_number}: {message}")
        self.page_number = page_number
