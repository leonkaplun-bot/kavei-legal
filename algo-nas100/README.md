# algo-nas100 — честный walk-forward для NAS100/US100 + cBot для FTMO-демо

Итог и все решения: **[REPORT.md](REPORT.md)** (первая строка — ответ «есть ли бот»).

```
fetch_data.py        скачать histdata.com NSXUSD M1 (2010→сегодня) и собрать data/NAS100_m1_NY_*.csv.gz (время Нью-Йорка)
orb_walkforward.py   движок: 8 стратегий, симулятор, издержки, walk-forward IS24/OOS6/шаг6, ворота
ftmo_layer.py        размер позиции под FTMO 50K + Монте-Карло P(пройти)/P(слить)
news/                календарь NFP/CPI/FOMC (NY) для фильтра новостей (+ build_news.py)
results/             таблицы окон, OOS-сделки, summary.json по каждому кандидату, эталонный месяц для сверки cBot
cbot/                Nas100FirstHourBreakoutFtmo.cs (cTrader cBot) + csproj для проверки компиляции
```

Запуск (Python 3.11+, pandas, numpy):
```
python fetch_data.py --download --build            # ~2 мин, 60 МБ
python orb_walkforward.py --strategy all            # все кандидаты, результаты в results/
python orb_walkforward.py --strategy orb_vol --news-file news/us_high_impact.csv --out results/news_on
python ftmo_layer.py --strategy orb_vol
```
