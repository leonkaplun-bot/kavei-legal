using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    /// <summary>
    /// LION RISK GUARDIAN
    ///
    /// Не торгует. Следит за счётом и не даёт нарушить правила FTMO,
    /// какой бы из твоих ботов ни открыл сделку.
    ///
    /// Ставится ОДИН раз на ОДИН график (любой символ, любой таймфрейм).
    /// Видит все позиции счёта, а не только свой символ.
    ///
    /// Что делает:
    ///   1. Режет объём позиции до заданного риска на сделку.
    ///   2. Вешает аварийный стоп на позицию без стопа.
    ///   3. Закрывает всё и запирает торговлю на день при своём дневном лимите.
    ///   4. Закрывает всё и запирает навсегда при своём общем лимите.
    ///   5. Не пускает вторую позицию из коррелированной группы в ту же сторону.
    ///   6. Держит лимит числа открытых позиций.
    ///   7. Уводит в ноль перед выходными и в окнах новостей.
    ///   8. Пишет журнал сделок в CSV, чтобы посчитать матожидание после издержек.
    ///
    /// СНАЧАЛА режим Monitor: ничего не трогает, только пишет в лог, что СДЕЛАЛ БЫ.
    /// Неделя на демо в Monitor, смотришь лог, потом переключаешь на Enforce.
    /// </summary>
    [Robot(AccessRights = AccessRights.FullAccess, AddIndicators = false)]
    public class RiskGuardian : Robot
    {
        public enum GuardMode
        {
            /// <summary>Только пишет в лог, что сделал бы. Ничего не меняет.</summary>
            Monitor,

            /// <summary>Реально режет объём, ставит стопы и закрывает позиции.</summary>
            Enforce
        }

        // ---------- режим ----------

        [Parameter("Режим", Group = "1. Режим", DefaultValue = GuardMode.Monitor)]
        public GuardMode Mode { get; set; }

        [Parameter("Стартовый баланс счёта (0 = взять текущий)", Group = "1. Режим", DefaultValue = 0.0, MinValue = 0)]
        public double ConfiguredStartBalance { get; set; }

        // ---------- риск ----------

        [Parameter("Риск на сделку, % от стартового баланса", Group = "2. Риск", DefaultValue = 0.25, MinValue = 0.01, MaxValue = 5.0)]
        public double RiskPercentPerTrade { get; set; }

        [Parameter("Свой дневной лимит, %", Group = "2. Риск", DefaultValue = 2.0, MinValue = 0.1, MaxValue = 10.0)]
        public double MyDailyLossPercent { get; set; }

        [Parameter("Свой общий лимит, %", Group = "2. Риск", DefaultValue = 6.0, MinValue = 0.5, MaxValue = 20.0)]
        public double MyTotalLossPercent { get; set; }

        [Parameter("Аварийный стоп, ATR(14) на D1 × этот множитель", Group = "2. Риск", DefaultValue = 0.5, MinValue = 0.05, MaxValue = 5.0)]
        public double EmergencyStopAtrMultiple { get; set; }

        // ---------- позиции ----------

        [Parameter("Максимум открытых позиций", Group = "3. Позиции", DefaultValue = 2, MinValue = 1, MaxValue = 20)]
        public int MaxOpenPositions { get; set; }

        [Parameter("Максимум позиций на один символ", Group = "3. Позиции", DefaultValue = 1, MinValue = 1, MaxValue = 10)]
        public int MaxPositionsPerSymbol { get; set; }

        [Parameter("Коррелированные группы (через ; внутри через ,)", Group = "3. Позиции", DefaultValue = "EURUSD,GBPUSD;GER40,DE40,US500,NAS100;XAUUSD,XAGUSD")]
        public string CorrelationGroups { get; set; }

        // ---------- время ----------

        [Parameter("Закрывать всё за N минут до конца пятницы", Group = "4. Время", DefaultValue = 60, MinValue = 0, MaxValue = 600)]
        public int FlatBeforeWeekendMinutes { get; set; }

        [Parameter("Конец торговой недели, час UTC (пятница)", Group = "4. Время", DefaultValue = 20, MinValue = 12, MaxValue = 23)]
        public int WeekEndHourUtc { get; set; }

        [Parameter("Файл новостей (datetime_utc,currency,tier,title)", Group = "4. Время", DefaultValue = "news_events.csv")]
        public string NewsFileName { get; set; }

        [Parameter("Блокировать торговлю за N минут до новости", Group = "4. Время", DefaultValue = 5, MinValue = 0, MaxValue = 120)]
        public int NewsBlockBeforeMinutes { get; set; }

        [Parameter("Блокировать торговлю N минут после новости", Group = "4. Время", DefaultValue = 5, MinValue = 0, MaxValue = 120)]
        public int NewsBlockAfterMinutes { get; set; }

        [Parameter("Минимальный tier новости для блокировки", Group = "4. Время", DefaultValue = 3, MinValue = 1, MaxValue = 3)]
        public int NewsMinTier { get; set; }

        // ---------- журнал ----------

        [Parameter("Писать журнал сделок в CSV", Group = "5. Журнал", DefaultValue = true)]
        public bool WriteTradeLog { get; set; }

        [Parameter("Имя файла журнала", Group = "5. Журнал", DefaultValue = "guardian_trades.csv")]
        public string TradeLogFileName { get; set; }

        // ---------- внутреннее состояние ----------

        private static readonly TimeSpan CheckInterval = TimeSpan.FromSeconds(1);

        private TimeZoneInfo _ftmoZone;
        private double _startBalance;
        private double _dayStartEquity;
        private DateTime _currentFtmoDay;
        private bool _dayLocked;
        private bool _accountLocked;
        private DateTime _lastCheck;
        private string _tradeLogPath;
        private readonly List<DateTime> _newsTimesUtc = new List<DateTime>();
        private readonly Dictionary<int, PositionSnapshot> _seen = new Dictionary<int, PositionSnapshot>();
        private readonly HashSet<int> _sizeChecked = new HashSet<int>();

        private sealed class PositionSnapshot
        {
            public int Id;
            public string Symbol;
            public string Label;
            public TradeType Direction;
            public DateTime EntryTimeUtc;
            public double EntryPrice;
            public double StopLoss;
            public double TakeProfit;
            public double VolumeInUnits;
            public double RiskMoneyAtEntry;
        }

        // =====================================================================

        protected override void OnStart()
        {
            _ftmoZone = FindZone("Europe/Prague", "Central European Standard Time", "Europe/Berlin", "W. Europe Standard Time");
            _startBalance = ConfiguredStartBalance > 0 ? ConfiguredStartBalance : Account.Balance;
            _currentFtmoDay = FtmoDayOf(Server.Time);
            _dayStartEquity = Account.Equity;
            _lastCheck = DateTime.MinValue;

            LoadNews();
            PrepareTradeLog();

            Positions.Opened += OnPositionOpened;
            Positions.Closed += OnPositionClosed;

            foreach (var position in Positions)
            {
                Remember(position);
            }

            Print("=== LION RISK GUARDIAN ===");
            Print("Режим: {0}{1}", Mode, Mode == GuardMode.Monitor ? "  (НИЧЕГО НЕ ТРОГАЮ, только пишу в лог)" : "  (ЗАЩИТА ВКЛЮЧЕНА)");
            Print("Стартовый баланс: {0:F2} {1}", _startBalance, Account.Currency);
            Print("Риск на сделку: {0:F2}% = {1:F2} {2}", RiskPercentPerTrade, RiskMoneyPerTrade(), Account.Currency);
            Print("Мой дневной лимит: {0:F2}% = {1:F2}   (у FTMO 5% на 2-step, 3% на 1-step)", MyDailyLossPercent, _startBalance * MyDailyLossPercent / 100.0);
            Print("Мой общий лимит: {0:F2}% = {1:F2}   (у FTMO 10%)", MyTotalLossPercent, _startBalance * MyTotalLossPercent / 100.0);
            Print("Максимум позиций: {0}, на символ: {1}", MaxOpenPositions, MaxPositionsPerSymbol);
            Print("Новостей загружено: {0}", _newsTimesUtc.Count);
            Print("Торговый день FTMO начался: {0:yyyy-MM-dd} (CE(S)T), эквити на старте {1:F2}", _currentFtmoDay, _dayStartEquity);

            var maxLossPerDay = RiskMoneyPerTrade() * MaxOpenPositions;
            var dailyCapMoney = _startBalance * MyDailyLossPercent / 100.0;
            if (maxLossPerDay >= dailyCapMoney)
            {
                Print("ВНИМАНИЕ: риск {0:F2} × {1} позиций = {2:F2}, это не меньше дневного лимита {3:F2}. Уменьши риск на сделку.",
                    RiskMoneyPerTrade(), MaxOpenPositions, maxLossPerDay, dailyCapMoney);
            }
        }

        protected override void OnTick()
        {
            if (Server.Time - _lastCheck < CheckInterval)
            {
                return;
            }

            _lastCheck = Server.Time;

            RollDayIfNeeded();
            CheckTotalLoss();
            CheckDailyLoss();
            CheckWeekendFlat();
            CheckNewsFlat();
            EnforcePositionRules();
        }

        protected override void OnStop()
        {
            Print("Guardian остановлен. Эквити {0:F2}, день {1:yyyy-MM-dd}, просадка за день {2:F2}",
                Account.Equity, _currentFtmoDay, Account.Equity - _dayStartEquity);
        }

        // ---------- торговый день FTMO ----------

        /// <summary>
        /// День FTMO считается с 00:00 до 23:59 по центральноевропейскому времени,
        /// а не по времени сервера и не по UTC.
        /// </summary>
        private DateTime FtmoDayOf(DateTime utc)
        {
            var local = TimeZoneInfo.ConvertTimeFromUtc(DateTime.SpecifyKind(utc, DateTimeKind.Utc), _ftmoZone);
            return local.Date;
        }

        private void RollDayIfNeeded()
        {
            var day = FtmoDayOf(Server.Time);
            if (day == _currentFtmoDay)
            {
                return;
            }

            _currentFtmoDay = day;
            _dayStartEquity = Account.Equity;
            _dayLocked = false;
            Print("--- новый торговый день {0:yyyy-MM-dd}, эквити на старте {1:F2}, замок снят ---", day, _dayStartEquity);
        }

        // ---------- лимиты ----------

        private double RiskMoneyPerTrade()
        {
            return _startBalance * RiskPercentPerTrade / 100.0;
        }

        private void CheckTotalLoss()
        {
            if (_accountLocked)
            {
                return;
            }

            var floor = _startBalance * (1.0 - MyTotalLossPercent / 100.0);
            if (Account.Equity > floor)
            {
                return;
            }

            _accountLocked = true;
            Print("СТОП СЧЁТА: эквити {0:F2} упало до моего общего лимита {1:F2}. Закрываю всё и больше не пускаю.", Account.Equity, floor);
            CloseEverything("общий лимит");
        }

        private void CheckDailyLoss()
        {
            if (_dayLocked || _accountLocked)
            {
                return;
            }

            var allowed = _startBalance * MyDailyLossPercent / 100.0;
            var lost = _dayStartEquity - Account.Equity;
            if (lost < allowed)
            {
                return;
            }

            _dayLocked = true;
            Print("СТОП ДНЯ: потеряно {0:F2} из разрешённых {1:F2}. Закрываю всё до конца дня {2:yyyy-MM-dd}.", lost, allowed, _currentFtmoDay);
            CloseEverything("дневной лимит");
        }

        private void CheckWeekendFlat()
        {
            if (FlatBeforeWeekendMinutes <= 0 || Positions.Count == 0)
            {
                return;
            }

            var now = Server.Time;
            if (now.DayOfWeek != DayOfWeek.Friday)
            {
                return;
            }

            var weekEnd = now.Date.AddHours(WeekEndHourUtc);
            if (now < weekEnd.AddMinutes(-FlatBeforeWeekendMinutes) || now >= weekEnd)
            {
                return;
            }

            Print("Пятница, до закрытия недели меньше {0} мин. Ухожу в ноль: переносить через выходные нечем не компенсируется.", FlatBeforeWeekendMinutes);
            CloseEverything("выходные");
        }

        private void CheckNewsFlat()
        {
            if (_newsTimesUtc.Count == 0 || Positions.Count == 0)
            {
                return;
            }

            var now = Server.Time;
            foreach (var newsTime in _newsTimesUtc)
            {
                if (now >= newsTime.AddMinutes(-NewsBlockBeforeMinutes) && now <= newsTime.AddMinutes(NewsBlockAfterMinutes))
                {
                    Print("Окно новости {0:yyyy-MM-dd HH:mm}Z. Ухожу в ноль: спред в такие минуты расходится в 5–20 раз.", newsTime);
                    CloseEverything("новость");
                    return;
                }
            }
        }

        private bool IsBlocked(out string reason)
        {
            if (_accountLocked)
            {
                reason = "счёт заперт по общему лимиту";
                return true;
            }

            if (_dayLocked)
            {
                reason = "день заперт по дневному лимиту";
                return true;
            }

            var now = Server.Time;
            foreach (var newsTime in _newsTimesUtc)
            {
                if (now >= newsTime.AddMinutes(-NewsBlockBeforeMinutes) && now <= newsTime.AddMinutes(NewsBlockAfterMinutes))
                {
                    reason = string.Format(CultureInfo.InvariantCulture, "окно новости {0:yyyy-MM-dd HH:mm}Z", newsTime);
                    return true;
                }
            }

            reason = null;
            return false;
        }

        // ---------- правила по позициям ----------

        private void EnforcePositionRules()
        {
            foreach (var position in Positions.ToArray())
            {
                EnsureStopLoss(position);
                EnsureSize(position);
            }
        }

        private void OnPositionOpened(PositionOpenedEventArgs args)
        {
            var position = args.Position;
            Remember(position);

            string reason;
            if (IsBlocked(out reason))
            {
                Print("ЗАКРЫВАЮ {0} #{1}: торговля запрещена ({2}).", position.SymbolName, position.Id, reason);
                Close(position, "запрет");
                return;
            }

            if (Positions.Count > MaxOpenPositions)
            {
                Print("ЗАКРЫВАЮ {0} #{1}: позиций {2}, разрешено {3}.", position.SymbolName, position.Id, Positions.Count, MaxOpenPositions);
                Close(position, "лимит позиций");
                return;
            }

            var sameSymbol = Positions.Where(p => string.Equals(p.SymbolName, position.SymbolName, StringComparison.OrdinalIgnoreCase)).Count();
            if (sameSymbol > MaxPositionsPerSymbol)
            {
                Print("ЗАКРЫВАЮ {0} #{1}: по символу {2} позиций, разрешено {3}.", position.SymbolName, position.Id, sameSymbol, MaxPositionsPerSymbol);
                Close(position, "лимит на символ");
                return;
            }

            var clash = FindCorrelationClash(position);
            if (clash != null)
            {
                Print("ЗАКРЫВАЮ {0} #{1}: уже открыт {2} в ту же сторону, это одна и та же ставка под дневным лимитом.",
                    position.SymbolName, position.Id, clash.SymbolName);
                Close(position, "корреляция");
                return;
            }

            EnsureStopLoss(position);
            EnsureSize(position);
        }

        private void OnPositionClosed(PositionClosedEventArgs args)
        {
            LogClosedTrade(args.Position, args.Reason);
            _seen.Remove(args.Position.Id);
            _sizeChecked.Remove(args.Position.Id);
        }

        private Position FindCorrelationClash(Position position)
        {
            var group = GroupOf(position.SymbolName);
            if (group == null)
            {
                return null;
            }

            foreach (var other in Positions)
            {
                if (other.Id == position.Id || other.TradeType != position.TradeType)
                {
                    continue;
                }

                if (string.Equals(other.SymbolName, position.SymbolName, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }

                var otherGroup = GroupOf(other.SymbolName);
                if (otherGroup != null && ReferenceEquals(otherGroup, group))
                {
                    return other;
                }
            }

            return null;
        }

        private readonly List<List<string>> _parsedGroups = new List<List<string>>();
        private bool _groupsParsed;

        private List<string> GroupOf(string symbol)
        {
            if (!_groupsParsed)
            {
                _groupsParsed = true;
                foreach (var raw in (CorrelationGroups ?? string.Empty).Split(';'))
                {
                    var members = raw.Split(',')
                        .Select(x => x.Trim())
                        .Where(x => x.Length > 0)
                        .ToList();
                    if (members.Count > 1)
                    {
                        _parsedGroups.Add(members);
                    }
                }
            }

            foreach (var group in _parsedGroups)
            {
                foreach (var member in group)
                {
                    if (symbol.IndexOf(member, StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        return group;
                    }
                }
            }

            return null;
        }

        // ---------- стоп ----------

        private void EnsureStopLoss(Position position)
        {
            if (position.StopLoss.HasValue)
            {
                return;
            }

            var symbol = Symbols.GetSymbol(position.SymbolName);
            if (symbol == null)
            {
                return;
            }

            var distance = EmergencyStopDistance(symbol);
            if (distance <= 0)
            {
                return;
            }

            var stop = position.TradeType == TradeType.Buy
                ? position.EntryPrice - distance
                : position.EntryPrice + distance;

            Print("{0} {1} #{2} БЕЗ СТОПА. {3} аварийный стоп на {4:F5} ({5:F1} пипсов).",
                Mode == GuardMode.Enforce ? "Ставлю" : "Поставил бы",
                position.SymbolName, position.Id,
                Mode == GuardMode.Enforce ? "Вешаю" : "Повесил бы",
                stop, distance / symbol.PipSize);

            if (Mode == GuardMode.Enforce)
            {
                var result = ModifyPosition(position, stop, position.TakeProfit);
                if (!result.IsSuccessful)
                {
                    Print("Не удалось поставить стоп на #{0}: {1}. ЗАКРЫВАЮ позицию, без стопа риск не ограничен.", position.Id, result.Error);
                    Close(position, "нет стопа");
                }
            }
        }

        private double EmergencyStopDistance(Symbol symbol)
        {
            var bars = MarketData.GetBars(TimeFrame.Daily, symbol.Name);
            if (bars == null || bars.Count < 15)
            {
                return symbol.PipSize * 50;
            }

            var sum = 0.0;
            var count = 0;
            for (var i = bars.Count - 15; i < bars.Count - 1; i++)
            {
                if (i < 1)
                {
                    continue;
                }

                var high = bars.HighPrices[i];
                var low = bars.LowPrices[i];
                var prevClose = bars.ClosePrices[i - 1];
                sum += Math.Max(high - low, Math.Max(Math.Abs(high - prevClose), Math.Abs(low - prevClose)));
                count++;
            }

            if (count == 0)
            {
                return symbol.PipSize * 50;
            }

            return sum / count * EmergencyStopAtrMultiple;
        }

        // ---------- объём ----------

        private void EnsureSize(Position position)
        {
            if (!position.StopLoss.HasValue || _sizeChecked.Contains(position.Id))
            {
                return;
            }

            var symbol = Symbols.GetSymbol(position.SymbolName);
            if (symbol == null)
            {
                return;
            }

            var stopPips = Math.Abs(position.EntryPrice - position.StopLoss.Value) / symbol.PipSize;
            if (stopPips <= 0)
            {
                return;
            }

            var riskPerUnit = stopPips * symbol.PipValue;
            if (riskPerUnit <= 0)
            {
                return;
            }

            var allowedUnits = symbol.NormalizeVolumeInUnits(RiskMoneyPerTrade() / riskPerUnit, RoundingMode.Down);
            var currentRisk = position.VolumeInUnits * riskPerUnit;

            _sizeChecked.Add(position.Id);

            if (position.VolumeInUnits <= allowedUnits || allowedUnits < symbol.VolumeInUnitsMin)
            {
                if (allowedUnits < symbol.VolumeInUnitsMin)
                {
                    Print("{0} #{1}: при риске {2:F2} допустимый объём меньше минимального лота. Стоп {3:F1} пипсов слишком широкий для такого риска.",
                        position.SymbolName, position.Id, RiskMoneyPerTrade(), stopPips);
                }

                return;
            }

            var excess = symbol.NormalizeVolumeInUnits(position.VolumeInUnits - allowedUnits, RoundingMode.Down);
            Print("{0} {1} #{2}: риск {3:F2} вместо {4:F2}. {5} объём с {6} до {7}.",
                Mode == GuardMode.Enforce ? "РЕЖУ" : "ОБРЕЗАЛ БЫ",
                position.SymbolName, position.Id, currentRisk, RiskMoneyPerTrade(),
                Mode == GuardMode.Enforce ? "Срезаю" : "Срезал бы",
                position.VolumeInUnits, allowedUnits);

            if (Mode == GuardMode.Enforce && excess >= symbol.VolumeInUnitsMin)
            {
                var result = ClosePosition(position, excess);
                if (!result.IsSuccessful)
                {
                    Print("Не удалось срезать объём на #{0}: {1}", position.Id, result.Error);
                }
            }
        }

        // ---------- закрытие ----------

        private void CloseEverything(string reason)
        {
            if (Mode == GuardMode.Monitor)
            {
                Print("[Monitor] Закрыл бы все {0} позиций. Причина: {1}.", Positions.Count, reason);
                return;
            }

            foreach (var position in Positions.ToArray())
            {
                var result = ClosePosition(position);
                if (!result.IsSuccessful)
                {
                    Print("Не удалось закрыть #{0} ({1}): {2}", position.Id, position.SymbolName, result.Error);
                }
            }
        }

        private void Close(Position position, string reason)
        {
            if (Mode == GuardMode.Monitor)
            {
                Print("[Monitor] Закрыл бы #{0} {1}. Причина: {2}.", position.Id, position.SymbolName, reason);
                return;
            }

            var result = ClosePosition(position);
            if (!result.IsSuccessful)
            {
                Print("Не удалось закрыть #{0}: {1}", position.Id, result.Error);
            }
        }

        // ---------- журнал ----------

        private void Remember(Position position)
        {
            if (_seen.ContainsKey(position.Id))
            {
                return;
            }

            var symbol = Symbols.GetSymbol(position.SymbolName);
            var risk = 0.0;
            if (symbol != null && position.StopLoss.HasValue)
            {
                var stopPips = Math.Abs(position.EntryPrice - position.StopLoss.Value) / symbol.PipSize;
                risk = position.VolumeInUnits * stopPips * symbol.PipValue;
            }

            _seen[position.Id] = new PositionSnapshot
            {
                Id = position.Id,
                Symbol = position.SymbolName,
                Label = position.Label ?? string.Empty,
                Direction = position.TradeType,
                EntryTimeUtc = position.EntryTime,
                EntryPrice = position.EntryPrice,
                StopLoss = position.StopLoss ?? 0.0,
                TakeProfit = position.TakeProfit ?? 0.0,
                VolumeInUnits = position.VolumeInUnits,
                RiskMoneyAtEntry = risk
            };
        }

        private void PrepareTradeLog()
        {
            if (!WriteTradeLog)
            {
                return;
            }

            try
            {
                var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "LionGuardian");
                Directory.CreateDirectory(dir);
                _tradeLogPath = Path.Combine(dir, TradeLogFileName);

                if (!File.Exists(_tradeLogPath))
                {
                    File.AppendAllText(_tradeLogPath,
                        "entry_utc,exit_utc,symbol,bot_label,direction,volume_units,entry_price,exit_price,stop_loss,take_profit," +
                        "risk_money,gross_profit,commission,swap,net_profit,r_multiple,close_reason,equity_after" + Environment.NewLine);
                }

                Print("Журнал сделок: {0}", _tradeLogPath);
            }
            catch (Exception ex)
            {
                Print("Не смог подготовить журнал: {0}. Проверь, что в настройках cBot стоит FullAccess.", ex.Message);
                _tradeLogPath = null;
            }
        }

        private void LogClosedTrade(Position position, PositionCloseReason reason)
        {
            if (!WriteTradeLog || _tradeLogPath == null)
            {
                return;
            }

            PositionSnapshot snap;
            if (!_seen.TryGetValue(position.Id, out snap))
            {
                snap = null;
            }

            var risk = snap != null && snap.RiskMoneyAtEntry > 0 ? snap.RiskMoneyAtEntry : 0.0;
            var net = position.NetProfit;
            var r = risk > 0 ? net / risk : 0.0;

            var inv = CultureInfo.InvariantCulture;
            var line = string.Join(",", new[]
            {
                (snap != null ? snap.EntryTimeUtc : position.EntryTime).ToString("yyyy-MM-dd HH:mm:ss", inv),
                Server.Time.ToString("yyyy-MM-dd HH:mm:ss", inv),
                position.SymbolName,
                Quote(snap != null ? snap.Label : position.Label),
                position.TradeType.ToString(),
                position.VolumeInUnits.ToString("F2", inv),
                position.EntryPrice.ToString("F5", inv),
                (position.CurrentPrice).ToString("F5", inv),
                (position.StopLoss ?? 0.0).ToString("F5", inv),
                (position.TakeProfit ?? 0.0).ToString("F5", inv),
                risk.ToString("F2", inv),
                position.GrossProfit.ToString("F2", inv),
                position.Commissions.ToString("F2", inv),
                position.Swap.ToString("F2", inv),
                net.ToString("F2", inv),
                r.ToString("F4", inv),
                reason.ToString(),
                Account.Equity.ToString("F2", inv)
            });

            try
            {
                File.AppendAllText(_tradeLogPath, line + Environment.NewLine);
            }
            catch (Exception ex)
            {
                Print("Не смог записать сделку в журнал: {0}", ex.Message);
            }
        }

        private static string Quote(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return string.Empty;
            }

            return value.IndexOf(',') >= 0 ? "\"" + value.Replace("\"", "'") + "\"" : value;
        }

        // ---------- новости ----------

        private void LoadNews()
        {
            try
            {
                var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "LionGuardian");
                var path = Path.Combine(dir, NewsFileName);
                if (!File.Exists(path))
                {
                    Print("Файла новостей нет ({0}). Блокировка по новостям ВЫКЛЮЧЕНА.", path);
                    return;
                }

                var lines = File.ReadAllLines(path);
                for (var i = 0; i < lines.Length; i++)
                {
                    var parts = lines[i].Split(',');
                    if (parts.Length < 3)
                    {
                        continue;
                    }

                    DateTime when;
                    if (!DateTime.TryParse(parts[0].Trim(), CultureInfo.InvariantCulture,
                            DateTimeStyles.AdjustToUniversal | DateTimeStyles.AssumeUniversal, out when))
                    {
                        continue;
                    }

                    int tier;
                    if (!int.TryParse(parts[2].Trim(), out tier) || tier < NewsMinTier)
                    {
                        continue;
                    }

                    _newsTimesUtc.Add(when);
                }

                _newsTimesUtc.Sort();
            }
            catch (Exception ex)
            {
                Print("Не смог прочитать новости: {0}", ex.Message);
            }
        }

        // ---------- таймзона ----------

        private static TimeZoneInfo FindZone(params string[] ids)
        {
            foreach (var id in ids)
            {
                try
                {
                    return TimeZoneInfo.FindSystemTimeZoneById(id);
                }
                catch (TimeZoneNotFoundException)
                {
                }
                catch (InvalidTimeZoneException)
                {
                }
            }

            return TimeZoneInfo.Utc;
        }
    }
}
