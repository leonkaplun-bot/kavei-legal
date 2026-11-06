# SpecFlow AI

B2B SaaS: PDF-схемы и ТЗ → каскад из 4 ИИ-агентов → закупочная спецификация (BOM) и КП в Excel.

```
PDF ──► [0] pdf_processor ──► [1] Vision Extractor ──► [2] Engineering Validator
                                                            │
        Excel КП ◄── [4] Estimator ◄── [3] Catalog Matcher ◄┘ (прайсы: SQLite + ChromaDB + RapidFuzz)
```

## Структура проекта

```
specflow-ai/
├── .env.example               конфигурация (скопировать в .env)
├── requirements.txt
├── pytest.ini
├── app.py                     [Фаза 5] UI: загрузка PDF/прайсов, live-лог агентов, предпросмотр, скачивание .xlsx
├── specflow/
│   ├── __init__.py
│   ├── config.py              Settings из .env, реестр моделей Claude (цены, лимиты Vision), расчёт $ за вызов, логирование
│   ├── exceptions.py          иерархия ошибок с сообщениями для пользователя
│   ├── normalization.py       позиционные обозначения (QF1…QF6, XT1:1-24), единицы, полюса, кривые
│   ├── schemas.py             Pydantic v2: PDF → 4 агента → КП, контракты ответов LLM, учёт токенов/стоимости
│   ├── pdf_processor.py       PyMuPDF: 300 DPI, тайлы под лимиты Vision, текстовый слой, таблицы, кэш, async
│   ├── agents/
│   │   ├── base.py            [Фаза 2] клиент Anthropic: retry/backoff, structured outputs, учёт стоимости, бюджет
│   │   ├── extractor.py       [Фаза 2] Агент 1 — Vision & OCR Extractor
│   │   ├── validator.py       [Фаза 2] Агент 2 — Engineering Validator + правила комплектации
│   │   ├── matcher.py         [Фаза 3] Агент 3 — Catalog & SKU Matcher
│   │   └── estimator.py       [Фаза 4] Агент 4 — Commercial Estimator
│   ├── catalog_engine.py      [Фаза 3] импорт прайсов CSV/XLSX → SQLite + ChromaDB, гибридный поиск
│   ├── excel_exporter.py      [Фаза 4] КП / BOM / инженерный аудит с формулами и стилями
│   └── pipeline.py            [Фаза 4] оркестратор: события, артефакты этапов, бюджет прогона
├── tests/
│   ├── conftest.py            синтетические PDF: схема А3 с перечнем, ТЗ, повёрнутый лист, скан, пароль
│   ├── test_pdf_processor.py
│   └── test_schemas.py
└── data/                      (создаётся автоматически, в git не попадает)
    ├── renders/               PNG страниц и тайлов + page.json/document.json (кэш по SHA-256)
    ├── runs/                  артефакты прогонов (JSON каждого этапа)
    ├── uploads/  exports/  logs/
    ├── catalog.db             [Фаза 3]
    └── chroma/                [Фаза 3]
```

## Установка (Windows, Python 3.11+)

```bat
cd specflow-ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

В `.env` укажите `ANTHROPIC_API_KEY` (для Фазы 1 ключ не нужен).

## Проверка Фазы 1 на своих чертежах

```bat
python -m specflow.pdf_processor "D:\Проекты\ЩР-1.pdf" --pages 1-5
python -m specflow.pdf_processor "D:\Проекты\ЩР-1.pdf" --model claude-opus-5-5
```

Покажет по каждой странице: формат листа, тип (чертёж / таблица / текст / скан),
число тайлов и таблиц, оценку токенов и стоимости Vision-анализа. Картинки — в `data\renders\…`.

## Тесты

```bat
python -m pytest
```

## Статус

- [x] Фаза 1 — архитектура, конфигурация, схемы данных, обработка PDF
- [ ] Фаза 2 — Агент 1 (Vision Extractor) и Агент 2 (Engineering Validator)
- [ ] Фаза 3 — индексация прайсов и Агент 3 (Catalog Matcher)
- [ ] Фаза 4 — Агент 4 (Estimator), Excel, оркестратор
- [ ] Фаза 5 — веб-интерфейс и инструкция по запуску
