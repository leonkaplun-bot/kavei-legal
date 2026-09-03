# LION_REGIME

Регим-адаптивный бот. **Фаза 2 — «Учёный»: размечает историю, не торгует.**
Отдельный проект, ноль зависимостей от боевых ботов Leon (v14 / v15).

Motto: тупо, скучно, рабочее. Учёный измеряет — не торгует.

## Структура

```
LION_REGIME/
  README.md                       ← этот файл
  REGIME_PROJECT_MEMORY.md        ← память проекта: что сделано / сломано / следующий шаг
  PARKING_LOT.md                  ← идеи «заодно», которые НЕ реализуются
  LionRegime.sln
  Directory.Build.props           ← общие правила сборки (warning = error, nullable on)
  src/
    LionRegime.Core/              ← чистая логика, net6.0, без cAlgo
      Sessions/                   ← слой 1 (готов)
      Calendar/                   ← IHolidayCalendar (интерфейс)
    LionRegime.Tagger/            ← cBot-обёртка для cTrader (следующие сессии)
  tests/
    LionRegime.Core.Tests/        ← xunit, net8.0
  analysis/                       ← Python/pandas по CSV-выходам (позже)
  data/                           ← news_events.csv, выходные tags_*.csv (в .gitignore)
```

## Слои

| # | Слой | Файл | Статус |
|---|---|---|---|
| 1 | Sessions | `src/LionRegime.Core/Sessions/SessionEngine.cs` | **готов, 94 теста** |
| 2 | Liquidity Map | `LiquidityMap.cs` | — |
| 3 | Regime Detector | `RegimeDetector.cs` | — |
| 3a | News Calendar | `NewsCalendar.cs` | — |
| 4 | Strategy Library | `Strategies/` | только интерфейс (фаза 2) |
| 5 | Risk Manager | `RiskManager.cs` | только интерфейс (фаза 2) |

## Сборка и тесты

Нужен .NET SDK 8 (Core собирается под net6.0 — тот же target, что у cBot cTrader).

```
dotnet build -c Release
dotnet test  -c Release
```

Сборка с `TreatWarningsAsErrors=true`: любой warning валит билд. Это Definition of Done.

## Слой 1 — Sessions: как это работает

- Вход: закрытые бары в хронологическом порядке — `OnBar(openTimeUtc, high, low)`.
- Все расчёты в UTC. `cAlgo` отдаёт `Bars.OpenTimes[]` и `Server.Time` в UTC, конвертация не нужна.
- Каждая сессия привязана к таймзоне **своего рынка** и задана в его wall-clock:

| Сессия | Якорь | Локально | Летом (UTC / IL) |
|---|---|---|---|
| ASIA | Asia/Tokyo | 08:00–16:00 | 23:00–07:00 / 02:00–10:00 |
| FRANKFURT | Europe/Berlin | 08:00–09:00 | 06:00–07:00 / 09:00–10:00 |
| LONDON | Europe/London | 08:00–12:30 | 07:00–11:30 / 10:00–14:30 |
| NY_PRE | America/New_York | 07:30–09:30 | 11:30–13:30 / 14:30–16:30 |
| NY_CASH | America/New_York | 09:30–12:00 | 13:30–16:00 / 16:30–19:00 |
| LONDON_CLOSE | Europe/London | 16:00–17:00 | 15:00–16:00 / 18:00–19:00 |
| NY_CLOSE | America/New_York | 15:00–16:00 | 19:00–20:00 / 22:00–23:00 |

  Летом это ровно таблица из ТЗ. Зимой границы двигаются вместе со своим рынком
  (NY-сессии на час раньше по Израилю в марте 8–27 и октябре 25 – ноябрь 1), а не с Израилем.
  DST считает `TimeZoneInfo` по системной tz-базе, хардкода смещений нет.
- Israel time — только отображение (`SessionState.TimeIsrael`, колонка `timestamp_il`).
- Пересечение окон: тег бара = сессия с **большим** `SessionTag` (FRANKFURT > ASIA, LONDON_CLOSE > NY_CASH,
  NY_PRE > LONDON). High/Low при этом копятся у **всех** активных сессий.
- `IsSessionOpen` = первые 15 минут окна (3 бара M5), `IsSessionClose` = последние 15.
- Выходные (Sat/Sun по локальной дате якоря) и праздники (`IHolidayCalendar`) → `DEAD`.
- Профиль инструмента: `SessionProfile.ForSymbol("XAUUSD")` → ASIA тегируется DEAD, но Asia H/L считается.
- `SessionState.Current[tag]` / `Previous[tag]` — диапазоны текущего и предыдущего дня для LiquidityMap.

Lookahead исключён по построению: движок видит только закрытые бары и бросает исключение при
подаче бара не по порядку.
