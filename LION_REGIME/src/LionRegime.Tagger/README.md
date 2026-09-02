# LionRegime.Tagger

cBot `LionRegimeTagger` для cTrader-бэктестера. Не торгует, пишет `tags_{symbol}.csv`.
Появится после слоёв 2–3a. Ссылается на `LionRegime.Core`, содержит только:
подписку на бары, вызовы слоёв и запись CSV. Ни одной строки торговой логики.
