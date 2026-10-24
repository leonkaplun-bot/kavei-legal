// Nas100FirstHourBreakoutFtmo.cs  --  cTrader cBot (cAlgo API, C#)
//
// Candidate "orb_vol" from orb_walkforward.py, live parameter set selected on IS 2024-10-17..2026-10-16:
//     filt=False | stop=rng | tp=None      (= plain first-hour range breakout, NO activity filter)
// STATUS: did NOT pass the walk-forward gates (OOS PF 1.157 < 1.2, max DD 11.7% > 8% at 0.5% risk).
//         Use on a DEMO account only. See REPORT.md.
//
// Rules (identical to the Python simulator):
//   * Trading day = New York time (robot TimeZone = Eastern with DST).
//   * Range = high/low of the M1 bars 09:30:00 .. 10:29:59 NY.
//   * At 10:30 place a buy stop at range high and a sell stop at range low (first fill wins, other order cancelled).
//     Entries allowed until 15:00 NY (pending orders cancelled at 15:00).
//   * Stop loss: RANGE mode = opposite side of the range; ATR mode = AtrMult x ATR(14, D1, simple MA).
//   * Take profit: TakeR x risk (0 = none).  Time exit: close at the open of the 15:56 bar (= close of the 15:55 bar).
//   * Optional activity filter: sum of M1 (high-low) over the range window > FilterMult x median of the previous 20 days.
//   * One trade per day, max one position.
//   * Sizing: RISK mode = RiskPct of InitialBalance divided by stop distance (what the backtest measured, in R),
//             FIXED mode = fixed lots.  FTMO US100.cash: contract size 1 => 1 lot = 1 USD per index point.
//   * FTMO guards: stop trading for the day at -DailyStopPct of the day-start balance/equity,
//                  stop forever at -TotalStopPct of InitialBalance (all positions closed, orders cancelled).
//   * News filter: no new entries within +-NewsWindowMin of the times listed in NewsFile (NY time, "yyyy-MM-dd HH:mm" per line
//     or csv with a time_ny column); pending orders are pulled during the window and re-placed after it.
//
// Attach to the US100.cash M1 chart.  AccessRights.FullAccess is only needed to read the news file.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.EasternStandardTime, AccessRights = AccessRights.FullAccess)]
    public class Nas100FirstHourBreakoutFtmo : Robot
    {
        // ---------------- strategy ----------------
        [Parameter("Range start hour (NY)", DefaultValue = 9, Group = "Strategy")]
        public int RangeStartHour { get; set; }
        [Parameter("Range start minute (NY)", DefaultValue = 30, Group = "Strategy")]
        public int RangeStartMinute { get; set; }
        [Parameter("Range minutes", DefaultValue = 60, MinValue = 5, Group = "Strategy")]
        public int RangeMinutes { get; set; }
        [Parameter("Last entry hour (NY)", DefaultValue = 15, Group = "Strategy")]
        public int LastEntryHour { get; set; }
        [Parameter("Last entry minute (NY)", DefaultValue = 0, Group = "Strategy")]
        public int LastEntryMinute { get; set; }
        [Parameter("Time exit hour (NY)", DefaultValue = 15, Group = "Strategy")]
        public int ExitHour { get; set; }
        [Parameter("Time exit minute (NY)", DefaultValue = 56, Group = "Strategy")]
        public int ExitMinute { get; set; }
        [Parameter("Stop mode (RANGE / ATR)", DefaultValue = "RANGE", Group = "Strategy")]
        public string StopMode { get; set; }
        [Parameter("ATR stop multiple", DefaultValue = 0.5, Group = "Strategy")]
        public double AtrMult { get; set; }
        [Parameter("Take profit in R (0 = none)", DefaultValue = 0.0, Group = "Strategy")]
        public double TakeR { get; set; }
        [Parameter("Activity filter", DefaultValue = false, Group = "Strategy")]
        public bool UseActivityFilter { get; set; }
        [Parameter("Activity filter multiple", DefaultValue = 1.5, Group = "Strategy")]
        public double FilterMult { get; set; }
        [Parameter("Min stop distance (points)", DefaultValue = 3.0, Group = "Strategy")]
        public double MinStopPoints { get; set; }

        // ---------------- sizing ----------------
        [Parameter("Sizing (RISK / FIXED)", DefaultValue = "RISK", Group = "Sizing")]
        public string SizingMode { get; set; }
        [Parameter("Risk % of initial balance per trade", DefaultValue = 0.25, Group = "Sizing")]
        public double RiskPct { get; set; }
        [Parameter("Fixed lots", DefaultValue = 0.5, Group = "Sizing")]
        public double FixedLots { get; set; }

        // ---------------- FTMO guards ----------------
        [Parameter("Initial balance", DefaultValue = 50000.0, Group = "FTMO")]
        public double InitialBalance { get; set; }
        [Parameter("Daily stop % (stop for the day)", DefaultValue = 3.0, Group = "FTMO")]
        public double DailyStopPct { get; set; }
        [Parameter("Total stop % (stop forever)", DefaultValue = 7.0, Group = "FTMO")]
        public double TotalStopPct { get; set; }

        // ---------------- news ----------------
        [Parameter("News filter", DefaultValue = true, Group = "News")]
        public bool UseNewsFilter { get; set; }
        [Parameter("News window (minutes)", DefaultValue = 15, Group = "News")]
        public int NewsWindowMin { get; set; }
        [Parameter("News file (NY times)", DefaultValue = "", Group = "News")]
        public string NewsFile { get; set; }

        private const string Label = "NAS100-FHB";
        private AverageTrueRange _atrD1;
        private readonly List<DateTime> _news = new List<DateTime>();
        private readonly List<double> _activityHistory = new List<double>();   // previous days' activity (for the filter)

        private DateTime _currentDay = DateTime.MinValue;
        private double _dayStartBalance;
        private bool _dayBlocked, _tradedToday, _ordersPlaced, _rangeReady, _stoppedForever;
        private double _rangeHigh, _rangeLow, _todayActivity;

        protected override void OnStart()
        {
            var daily = MarketData.GetBars(TimeFrame.Daily);
            _atrD1 = Indicators.AverageTrueRange(daily, 14, MovingAverageType.Simple);
            LoadNews();
            BackfillActivity();
            Positions.Opened += OnPositionOpened;
            Print("Started. Symbol {0}, PipSize {1}, PipValue {2}, usd/point/lot {3:F2}", SymbolName, Symbol.PipSize, Symbol.PipValue, UsdPerPointPerLot());
        }

        private double UsdPerPointPerLot()
        {
            // PipValue = account-currency value of one pip for one lot; divide by PipSize to get value per 1.0 price unit (one index point)
            return Symbol.PipValue / Symbol.PipSize;
        }

        private TimeSpan T(int h, int m) { return new TimeSpan(h, m, 0); }

        protected override void OnTick()
        {
            if (_stoppedForever) return;
            // FTMO guards on every tick (equity based)
            if (Account.Equity <= InitialBalance * (1.0 - TotalStopPct / 100.0))
            {
                Print("TOTAL STOP hit: equity {0:F2}. Closing everything and stopping forever.", Account.Equity);
                FlattenAll(); _stoppedForever = true; Stop(); return;
            }
            if (!_dayBlocked && _dayStartBalance > 0 && Account.Equity <= _dayStartBalance * (1.0 - DailyStopPct / 100.0))
            {
                Print("DAILY STOP hit: equity {0:F2} vs day start {1:F2}. No more trading today.", Account.Equity, _dayStartBalance);
                FlattenAll(); _dayBlocked = true;
            }
        }

        protected override void OnBar()
        {
            if (_stoppedForever) return;
            var now = Bars.OpenTimes.LastValue;            // open time of the bar that just opened = close time of the last closed bar (NY time)
            if (now.Date != _currentDay)
                StartNewDay(now);

            var tod = now.TimeOfDay;
            var rangeStart = T(RangeStartHour, RangeStartMinute);
            var rangeEnd = rangeStart + TimeSpan.FromMinutes(RangeMinutes);
            var lastEntry = T(LastEntryHour, LastEntryMinute);
            var timeExit = T(ExitHour, ExitMinute);

            // 1) time exit: the bar before timeExit just closed
            if (tod >= timeExit)
            {
                foreach (var p in Positions.FindAll(Label, SymbolName)) ClosePosition(p);
                CancelOrders();
                return;
            }
            // 2) last entry time: pull pending orders
            if (tod >= lastEntry)
            {
                if (_ordersPlaced) { CancelOrders(); _ordersPlaced = false; }
                return;
            }
            // 3) build the range exactly when the first post-range bar opens
            if (!_rangeReady && tod >= rangeEnd)
            {
                BuildRange(now.Date, rangeStart, rangeEnd);
                _rangeReady = true;
                if (UseActivityFilter)
                {
                    _activityHistory.Add(_todayActivity);
                    var prev = _activityHistory.Take(_activityHistory.Count - 1).ToList();
                    if (prev.Count >= 15)
                    {
                        var med = Median(prev.Skip(Math.Max(0, prev.Count - 20)));
                        if (_todayActivity <= FilterMult * med) { Print("Activity filter: {0:F1} <= {1:F1}. No trade today.", _todayActivity, FilterMult * med); _tradedToday = true; }
                    }
                    else { Print("Activity filter: not enough history ({0} days). No trade today.", prev.Count); _tradedToday = true; }
                }
            }
            // 4) place / re-place the breakout orders
            if (_rangeReady && !_tradedToday && !_dayBlocked && Positions.FindAll(Label, SymbolName).Length == 0)
            {
                bool inNews = UseNewsFilter && IsNewsTime(now);
                if (inNews && _ordersPlaced) { CancelOrders(); _ordersPlaced = false; Print("News window: pending orders pulled."); }
                else if (!inNews && !_ordersPlaced) PlaceBreakoutOrders();
            }
        }

        private void StartNewDay(DateTime now)
        {
            _currentDay = now.Date;
            _dayStartBalance = Math.Max(Account.Balance, Account.Equity);
            _dayBlocked = false; _tradedToday = false; _ordersPlaced = false; _rangeReady = false;
            _rangeHigh = double.MinValue; _rangeLow = double.MaxValue; _todayActivity = 0;
            CancelOrders();
        }

        private void BuildRange(DateTime day, TimeSpan rangeStart, TimeSpan rangeEnd)
        {
            int n = 0; _rangeHigh = double.MinValue; _rangeLow = double.MaxValue; _todayActivity = 0;
            for (int i = Bars.Count - 2; i >= 0; i--)          // closed bars only
            {
                var t = Bars.OpenTimes[i];
                if (t.Date != day || t.TimeOfDay < rangeStart) break;
                if (t.TimeOfDay >= rangeEnd) continue;
                _rangeHigh = Math.Max(_rangeHigh, Bars.HighPrices[i]);
                _rangeLow = Math.Min(_rangeLow, Bars.LowPrices[i]);
                _todayActivity += Bars.HighPrices[i] - Bars.LowPrices[i];
                n++;
            }
            if (n < Math.Max(5, RangeMinutes - 10))
            {
                Print("Range incomplete ({0} bars) - no trade today.", n); _tradedToday = true; return;
            }
            Print("Range {0:HH:mm}-{1:HH:mm}: high {2} low {3} ({4} bars, activity {5:F1})", day + rangeStart, day + rangeEnd, _rangeHigh, _rangeLow, n, _todayActivity);
        }

        private void PlaceBreakoutOrders()
        {
            double atr = _atrD1.Result.Last(1);
            double buyStopPts, sellStopPts;
            if (StopMode.Trim().ToUpperInvariant() == "ATR")
            {
                if (double.IsNaN(atr) || atr <= 0) { Print("ATR not ready - no trade."); _tradedToday = true; return; }
                buyStopPts = sellStopPts = AtrMult * atr;
            }
            else
            {
                buyStopPts = sellStopPts = _rangeHigh - _rangeLow;
            }
            if (buyStopPts < MinStopPoints) { Print("Stop {0:F2} < min {1} - no trade today.", buyStopPts, MinStopPoints); _tradedToday = true; return; }

            double volBuy = VolumeForStop(buyStopPts), volSell = VolumeForStop(sellStopPts);
            if (volBuy <= 0 || volSell <= 0) { Print("Volume below minimum - no trade today."); _tradedToday = true; return; }
            // absolute protection levels, computed from the order level (RANGE mode => stop = other side of the range)
            double slBuy = _rangeHigh - buyStopPts, slSell = _rangeLow + sellStopPts;
            double? tpBuy = TakeR > 0 ? (double?)(_rangeHigh + TakeR * buyStopPts) : null;
            double? tpSell = TakeR > 0 ? (double?)(_rangeLow - TakeR * sellStopPts) : null;

            var r1 = PlaceStopOrder(TradeType.Buy, SymbolName, volBuy, _rangeHigh, Label, slBuy, tpBuy, ProtectionType.Absolute);
            var r2 = PlaceStopOrder(TradeType.Sell, SymbolName, volSell, _rangeLow, Label, slSell, tpSell, ProtectionType.Absolute);
            _ordersPlaced = r1.IsSuccessful || r2.IsSuccessful;
            Print("Orders: buy stop {0} ({1} units, sl {2:F1} pts) {3} | sell stop {4} ({5} units) {6}",
                  _rangeHigh, volBuy, buyStopPts, r1.IsSuccessful ? "ok" : r1.Error.ToString(), _rangeLow, volSell, r2.IsSuccessful ? "ok" : r2.Error.ToString());
            // a stop order can be filled immediately if price is already beyond the level (gap) -> handled in OnPositionOpened
        }

        private double VolumeForStop(double stopPts)
        {
            double lots;
            if (SizingMode.Trim().ToUpperInvariant() == "FIXED") lots = FixedLots;
            else
            {
                double riskUsd = InitialBalance * RiskPct / 100.0;
                lots = riskUsd / (stopPts * UsdPerPointPerLot());
            }
            double units = Symbol.QuantityToVolumeInUnits(lots);
            units = Symbol.NormalizeVolumeInUnits(units, RoundingMode.Down);
            if (units < Symbol.VolumeInUnitsMin) return 0;
            if (units > Symbol.VolumeInUnitsMax) units = Symbol.VolumeInUnitsMax;
            return units;
        }

        private void OnPositionOpened(PositionOpenedEventArgs e)
        {
            if (e.Position.Label != Label || e.Position.SymbolName != SymbolName) return;
            _tradedToday = true;
            CancelOrders(); _ordersPlaced = false;              // one trade per day: drop the opposite order
            Print("ENTRY {0} {1} units @ {2}  SL {3}  TP {4}", e.Position.TradeType, e.Position.VolumeInUnits, e.Position.EntryPrice, e.Position.StopLoss, e.Position.TakeProfit);
            if (_dayBlocked) ClosePosition(e.Position);
        }

        private void CancelOrders()
        {
            foreach (var o in PendingOrders.Where(o => o.Label == Label && o.SymbolName == SymbolName).ToList()) CancelPendingOrder(o);
        }

        private void FlattenAll()
        {
            foreach (var p in Positions.FindAll(Label, SymbolName)) ClosePosition(p);
            CancelOrders(); _ordersPlaced = false;
        }

        private bool IsNewsTime(DateTime now)
        {
            foreach (var t in _news)
                if (Math.Abs((now - t).TotalMinutes) <= NewsWindowMin) return true;
            return false;
        }

        private void LoadNews()
        {
            if (string.IsNullOrWhiteSpace(NewsFile)) return;
            try
            {
                foreach (var raw in System.IO.File.ReadAllLines(NewsFile))
                {
                    var line = raw.Trim(); if (line.Length == 0 || line.StartsWith("time_ny")) continue;
                    var s = line.Split(',')[0].Trim();
                    DateTime t;
                    if (DateTime.TryParseExact(s, new[] { "yyyy-MM-dd HH:mm", "yyyy-MM-dd H:mm", "yyyy-MM-ddTHH:mm" }, CultureInfo.InvariantCulture, DateTimeStyles.None, out t))
                        _news.Add(t);
                }
                Print("News filter: {0} events loaded from {1}", _news.Count, NewsFile);
            }
            catch (Exception ex) { Print("News file could not be read ({0}); filter inactive.", ex.Message); }
        }

        private void BackfillActivity()
        {
            // rebuild the per-day activity history from loaded M1 history so the filter works from day one
            if (!UseActivityFilter) return;
            var rangeStart = T(RangeStartHour, RangeStartMinute); var rangeEnd = rangeStart + TimeSpan.FromMinutes(RangeMinutes);
            DateTime day = DateTime.MinValue; double act = 0; int n = 0;
            for (int i = 0; i < Bars.Count - 1; i++)
            {
                var t = Bars.OpenTimes[i];
                if (t.Date != day)
                {
                    if (n >= Math.Max(5, RangeMinutes - 10)) _activityHistory.Add(act);
                    day = t.Date; act = 0; n = 0;
                }
                if (t.TimeOfDay >= rangeStart && t.TimeOfDay < rangeEnd) { act += Bars.HighPrices[i] - Bars.LowPrices[i]; n++; }
            }
            Print("Activity history backfilled: {0} days", _activityHistory.Count);
        }

        private static double Median(IEnumerable<double> xs)
        {
            var a = xs.OrderBy(x => x).ToArray(); if (a.Length == 0) return double.NaN;
            return a.Length % 2 == 1 ? a[a.Length / 2] : 0.5 * (a[a.Length / 2 - 1] + a[a.Length / 2]);
        }

        protected override void OnStop()
        {
            Positions.Opened -= OnPositionOpened;
        }
    }
}
