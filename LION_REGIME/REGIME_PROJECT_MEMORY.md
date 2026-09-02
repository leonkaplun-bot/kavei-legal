# REGIME_PROJECT_MEMORY

Память проекта LION_REGIME. Обновляется в конце каждой сессии: что сделано, что сломано, следующий шаг.
Локальная копия для auto-memory: `C:\Users\leonk\.claude\projects\C--JEAN-CLODE-VSEM-DAM-BOT\memory\REGIME_PROJECT_MEMORY.md`.

Версия: **LionRegime_v0.1** (слой 1). v0.2 — только после закрытия DoD слоя 2.

---

## Статус слоёв

| Слой | Статус | Тесты |
|---|---|---|
| 1 Sessions | готов | 94 / 94 |
| 2 Liquidity Map | не начат | — |
| 3 Regime Detector | не начат | — |
| 3a News Calendar | не начат | — |
| 4 Strategy Library | не начат (только интерфейс в фазе 2) | — |
| 5 Risk Manager | не начат (только интерфейс в фазе 2) | — |
| Tagger (cBot) | не начат | — |

## Открытые вопросы к Leon'у

**Блокирующие для следующих слоёв (не для слоя 1):**

1. **Timezone cTrader-сервера FTMO.** Для кода не нужен: cAlgo отдаёт `Bars.OpenTimes[]` и
   `Server.Time` в UTC независимо от отображения в терминале, и SessionEngine работает в UTC.
   Проверка одной строкой в любом cBot: `Print(Server.Time.Kind, " ", Server.TimeInUtc);`
   Если Kind = Utc — вопрос закрыт. Отображение графика (`Application.UserTimeOffset`) на код не влияет.
2. **История M5 XAUUSD за март–август 2026 в cTrader FTMO** — проверяет Leon. Нет истории → золото откладывается.
3. **Экспорт high-impact ForexFactory за 6 месяцев** — руками (26 недель по фильтру High) или ищем альтернативу.
   Нужно к слою 3a, не раньше.

**Не блокирующие:**

4. DXY и US10Y как символы в cTrader FTMO → иначе `dxyCorr`, `us10yDelta` в P1.
5. Праздники: хардкод основных или CSV. Пока `IHolidayCalendar` + `NoHolidays`.

## Решения, принятые без Leon'а (сессия 1) — можно отменить

| Решение | Почему | Где |
|---|---|---|
| Сессии привязаны к таймзоне своего рынка (Tokyo / Berlin / London / New York), заданы в его wall-clock | Единственный способ «DST обрабатывать явно» без хардкода. Летом совпадает с таблицей ТЗ 1:1. Зимой NY-сессии по Израилю на час раньше в окна 08–27.03 и 25.10–01.11 — это правильно: NYSE открывается в 09:30 ET, а не в 16:30 IL | `SessionSchedule.DefaultDefinitions` |
| ASIA привязана к Asia/Tokyo | Токио без DST → 23:00–07:00 UTC круглый год; зимой по Израилю 01:00–09:00 | там же |
| Пересечение окон: побеждает сессия с большим `SessionTag` | FRANKFURT > ASIA, NY_PRE > LONDON, LONDON_CLOSE > NY_CASH. Более узкое/позднее окно информативнее. H/L считаются у всех | `SessionTag`, `SessionSchedule.Classify` |
| `IsSessionOpen` / `IsSessionClose` = 15 минут (3 бара M5) | В ТЗ N не задано | `SessionSchedule.DefaultOpenWindowMinutes` |
| Бар классифицируется по времени открытия | Стандарт cTrader; бар [10:00, 10:05) принадлежит сессии, содержащей 10:00 | `SessionSchedule.Classify` |
| Выходные = Sat/Sun по локальной дате якоря → DEAD | ASIA понедельника (Tokyo Mon 08:00 = Sun 23:00 UTC) не выходной; суббота Tokyo = пятница 23:00 UTC → DEAD. FX-открытие воскресенья 22:00 UTC до 23:00 → DEAD | `SessionDefinition.WindowFor` |
| Gold: ASIA → тег DEAD, но Asia H/L копится | Asia range нужен детектору и карте ликвидности | `SessionProfile.Gold` |
| Core = net6.0, тесты = net8.0 | net6.0 — target cBot-проектов cTrader; тесты гоняем на SDK 8 | csproj |

## Лог сессий

### Сессия 1 — 2026-09-02

**Сделано:**
- Структура `LION_REGIME/`, solution, `Directory.Build.props` (warning = error, nullable on).
- Слой 1 полностью: `SessionTag`, `SessionRole`, `TimeZones`, `SessionDefinition`, `SessionWindow`,
  `SessionProfile`, `SessionSchedule`, `SessionSlot`, `SessionRange`, `SessionState`, `SessionEngine`,
  `IHolidayCalendar` + `NoHolidays`.
- 94 xunit-теста: правила DST 2026 всех четырёх зон по системной tz-базе; окна каждой сессии в UTC и в
  Israel time в шести периодах (полная зима → только US DST → IL DST без EU → полное лето → EU/IL зима при US DST →
  полная зима); приоритет пересечений; open/close-флаги; DEAD-минуты; выходные; инварианты на весь 2026
  (каждый будний день — ровно одно окно каждой сессии, длительность не зависит от DST, Classify не падает
  ни на одном M5-баре года); движок (диапазоны, ротация previous, gold-профиль, праздник, защита от
  нехронологичных баров).
- Сборка: 0 warnings, 0 errors. Тесты: 94 / 94.

**Сломано / известные ограничения:**
- Ночные сессии (через полночь локальной зоны) не поддерживаются — в дефолтах их нет.
- `MinutesIntoSession` для бара с `Session = DEAD` из-за роли Off (gold ASIA) — это минуты внутри окна
  `WindowTag`, а не «минуты с конца последней сессии». Осознанно, для консистентности CSV смотреть `WindowTag`.

**Не сделано (вне сессии 1 по плану):**
- cBot-обёртка `LionRegimeTagger`, слои 2–5, CSV-запись.
- Копия памяти в локальную папку auto-memory — окружение этой сессии не видит `C:\Users\leonk\...`.

**Ручная проверка Leon'ом перед слоем 2:**
- Открыть график любого инструмента за 01.04.2026 и 04.03.2026, сверить границы LONDON и NY_CASH по
  таблице в README с тем, что показывает cTrader (с поправкой на UserTimeOffset).
- Подтвердить или отменить приоритет LONDON_CLOSE > NY_CASH для золота.

**Следующий шаг:** слой 2 — `LiquidityMap.cs`. Вход: закрытые бары M5 + `SessionState` (диапазоны сессий).
Пулы PDH/PDL, PWH/PWL, PMH/PML, сессионные, EQH/EQL (k = 0.15 × ATR14), фрактальные свинги N = 5 на H1/H4.
Главное: `GetTargets` с тестами на NEAR vs FAR — известный failure mode прошлого бота.
Логировать body-sweep и wick-sweep отдельно (research-флаг 11/06, +26.8R).
