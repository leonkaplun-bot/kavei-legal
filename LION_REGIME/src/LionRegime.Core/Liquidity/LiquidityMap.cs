using System;
using System.Collections.Generic;
using LionRegime.Core.Indicators;
using LionRegime.Core.Market;
using LionRegime.Core.Sessions;

namespace LionRegime.Core.Liquidity;

/// <summary>
/// Слой 2 — карта ликвидности. Таблица пулов, пересчитывается на закрытии каждого бара.
/// Только закрытые бары. Ни одной строки торговой логики.
///
/// Как кормить (порядок важен, так же будет делать таггер):
///   1) закрытые бары старших ТФ — <see cref="OnHigherTimeframeBar"/> (D1/W1/MN1 дают дневные/недельные/месячные
///      пулы, H1/H4 — свинги, равные хаи/лои и ATR);
///   2) закрытый бар M5 — <see cref="OnBar"/> вместе с состоянием сессии из слоя 1.
///
/// Защита от lookahead не зависит от порядка подачи: у каждого пула есть CreatedAt (момент, когда он стал
/// известен), и бар с более ранним временем этот пул не видит.
///
/// Единица измерения расстояний и глубины свипа — ATR(14) на H1. Пока H1-ATR не готов, значения NaN,
/// а фильтр максимального расстояния отключён.
/// </summary>
public sealed class LiquidityMap
{
    private static readonly PoolType[] EmptyTypes = Array.Empty<PoolType>();

    private readonly LiquidityMapSettings _settings;
    private readonly List<LiquidityPool> _pools = new List<LiquidityPool>();
    private readonly List<SweepEvent> _pending = new List<SweepEvent>();
    private readonly Dictionary<Timeframe, AtrCalculator> _atr = new Dictionary<Timeframe, AtrCalculator>();
    private readonly Dictionary<Timeframe, SwingDetector> _swings = new Dictionary<Timeframe, SwingDetector>();
    private readonly Dictionary<(Timeframe Tf, PoolSide Side), List<Swing>> _swingHistory =
        new Dictionary<(Timeframe, PoolSide), List<Swing>>();
    private readonly Dictionary<Timeframe, DateTime> _lastHtfBar = new Dictionary<Timeframe, DateTime>();
    private readonly HashSet<string> _sessionRangesSeen = new HashSet<string>(StringComparer.Ordinal);

    private long _nextPoolId = 1;
    private DateTime? _lastBarUtc;

    public LiquidityMap(LiquidityMapSettings? settings = null)
    {
        _settings = settings ?? new LiquidityMapSettings();
        _settings.Validate();

        foreach (var tf in new[] { Timeframe.H1, Timeframe.H4 })
        {
            _atr[tf] = new AtrCalculator(_settings.AtrPeriod);
            _swings[tf] = new SwingDetector(tf, _settings.SwingPeriod);
            _swingHistory[(tf, PoolSide.High)] = new List<Swing>();
            _swingHistory[(tf, PoolSide.Low)] = new List<Swing>();
        }
    }

    public LiquidityMapSettings Settings => _settings;

    /// <summary>ATR(14, H1) — общий эталон расстояний. NaN, пока не готов.</summary>
    public double DistanceAtr => _atr[Timeframe.H1].Value;

    public double AtrOf(Timeframe tf) => _atr.TryGetValue(tf, out var atr) ? atr.Value : double.NaN;

    public IReadOnlyList<LiquidityPool> Pools => _pools;

    public int BarsProcessed { get; private set; }

    public DateTime? LastBarUtc => _lastBarUtc;

    /// <summary>События свипа, у которых окно возврата ещё не закрылось.</summary>
    public IReadOnlyList<SweepEvent> PendingSweeps => _pending;

    /// <summary>
    /// Закрытый бар старшего таймфрейма. D1/W1/MN1 → пулы предыдущего дня/недели/месяца.
    /// H1/H4 → ATR, фрактальные свинги и кластеры равных хаёв/лоёв.
    /// </summary>
    public IReadOnlyList<LiquidityPool> OnHigherTimeframeBar(Timeframe tf, Bar bar)
    {
        if (tf == Timeframe.M5)
        {
            throw new ArgumentException("M5 bars go to OnBar, not OnHigherTimeframeBar", nameof(tf));
        }

        if (_lastHtfBar.TryGetValue(tf, out var last) && bar.OpenTimeUtc <= last)
        {
            throw new InvalidOperationException($"{tf} bars must be strictly chronological: got {bar.OpenTimeUtc:O} after {last:O}");
        }

        _lastHtfBar[tf] = bar.OpenTimeUtc;
        var createdAt = Timeframes.CloseTimeOf(tf, bar.OpenTimeUtc);
        var created = new List<LiquidityPool>();

        switch (tf)
        {
            case Timeframe.D1:
                created.Add(AddPool(PoolType.PDH, bar.High, tf, createdAt));
                created.Add(AddPool(PoolType.PDL, bar.Low, tf, createdAt));
                break;
            case Timeframe.W1:
                created.Add(AddPool(PoolType.PWH, bar.High, tf, createdAt));
                created.Add(AddPool(PoolType.PWL, bar.Low, tf, createdAt));
                break;
            case Timeframe.MN1:
                created.Add(AddPool(PoolType.PMH, bar.High, tf, createdAt));
                created.Add(AddPool(PoolType.PML, bar.Low, tf, createdAt));
                break;
            case Timeframe.H1:
            case Timeframe.H4:
                _atr[tf].OnBar(bar);
                foreach (var swing in _swings[tf].OnBar(bar))
                {
                    created.Add(AddPool(swing.Side == PoolSide.High ? PoolType.SWING_H : PoolType.SWING_L, swing.Price, tf, swing.ConfirmedAt));
                    var equal = TryBuildEqualPool(tf, swing);
                    if (equal != null)
                    {
                        created.Add(equal);
                    }

                    RememberSwing(tf, swing);
                }

                break;
            default:
                throw new ArgumentOutOfRangeException(nameof(tf), tf, "Unsupported higher timeframe");
        }

        return created;
    }

    /// <summary>
    /// Закрытый бар M5. Создаёт сессионные пулы из завершившихся диапазонов слоя 1,
    /// двигает окна возврата и ищет новые свипы.
    /// </summary>
    public LiquidityUpdate OnBar(Bar bar, SessionState? session = null)
    {
        if (_lastBarUtc.HasValue && bar.OpenTimeUtc <= _lastBarUtc.Value)
        {
            throw new InvalidOperationException($"Bars must be strictly chronological: got {bar.OpenTimeUtc:O} after {_lastBarUtc.Value:O}");
        }

        if (session != null && session.TimeUtc != bar.OpenTimeUtc)
        {
            throw new ArgumentException($"SessionState time {session.TimeUtc:O} does not match bar time {bar.OpenTimeUtc:O}", nameof(session));
        }

        _lastBarUtc = bar.OpenTimeUtc;
        BarsProcessed++;

        var newPools = session is null ? (IReadOnlyList<LiquidityPool>)Array.Empty<LiquidityPool>() : HarvestSessionPools(session);
        var resolved = new List<SweepEvent>();
        AdvancePending(bar, resolved);
        var newSweeps = DetectSweeps(bar, session?.Session ?? SessionTag.DEAD, resolved);
        Prune(bar.OpenTimeUtc);

        return newPools.Count == 0 && resolved.Count == 0 && newSweeps.Count == 0
            ? LiquidityUpdate.Empty
            : new LiquidityUpdate(newSweeps, resolved, newPools);
    }

    /// <summary>Несобранные пулы, известные на момент последнего бара.</summary>
    public IReadOnlyList<LiquidityPool> ActivePools(DateTime? asOf = null)
    {
        var t = asOf ?? _lastBarUtc ?? DateTime.MaxValue;
        var result = new List<LiquidityPool>();
        foreach (var pool in _pools)
        {
            if (pool.IsActiveAt(t))
            {
                result.Add(pool);
            }
        }

        return result;
    }

    /// <summary>
    /// Несобранные пулы в заданную сторону, по возрастанию расстояния от цены.
    ///
    /// Long — пулы строго ВЫШЕ цены, Far = максимальная цена в пределах MaxDistanceAtr.
    /// Short — пулы строго НИЖЕ цены, Far = минимальная цена в пределах MaxDistanceAtr.
    ///
    /// Тейк ставится на Far. Near — это где нас стопят. Инверсия этих двух убила edge прошлого бота.
    /// </summary>
    public TargetSet GetTargets(TradeDirection direction, double currentPrice, DateTime? asOf = null, IReadOnlyList<PoolType>? onlyTypes = null)
    {
        if (double.IsNaN(currentPrice))
        {
            throw new ArgumentException("Current price must not be NaN", nameof(currentPrice));
        }

        var t = asOf ?? _lastBarUtc ?? DateTime.MaxValue;
        var atr = DistanceAtr;
        var hasLimit = atr > 0 && !double.IsNaN(atr);
        var maxDistance = hasLimit ? atr * _settings.MaxDistanceAtr : double.PositiveInfinity;
        var types = onlyTypes ?? EmptyTypes;
        var wantsAbove = direction == TradeDirection.Long;

        var matched = new List<LiquidityPool>();
        foreach (var pool in _pools)
        {
            if (!pool.IsActiveAt(t))
            {
                continue;
            }

            var distance = wantsAbove ? pool.Price - currentPrice : currentPrice - pool.Price;
            if (distance <= 0 || distance > maxDistance)
            {
                continue;
            }

            if (types.Count > 0 && !Contains(types, pool.Type))
            {
                continue;
            }

            matched.Add(pool);
        }

        matched.Sort((a, b) =>
        {
            var da = wantsAbove ? a.Price - currentPrice : currentPrice - a.Price;
            var db = wantsAbove ? b.Price - currentPrice : currentPrice - b.Price;
            var byDistance = da.CompareTo(db);
            return byDistance != 0 ? byDistance : a.Id.CompareTo(b.Id);
        });

        return new TargetSet(direction, currentPrice, atr, matched);
    }

    private static bool Contains(IReadOnlyList<PoolType> types, PoolType type)
    {
        for (var i = 0; i < types.Count; i++)
        {
            if (types[i] == type)
            {
                return true;
            }
        }

        return false;
    }

    private static PoolType? SessionPoolType(SessionTag tag, PoolSide side)
    {
        switch (tag)
        {
            case SessionTag.ASIA:
                return side == PoolSide.High ? PoolType.ASIA_H : PoolType.ASIA_L;
            case SessionTag.LONDON:
                return side == PoolSide.High ? PoolType.LONDON_H : PoolType.LONDON_L;
            case SessionTag.NY_CASH:
                return side == PoolSide.High ? PoolType.NY_H : PoolType.NY_L;
            default:
                // ТЗ задаёт пулы только для ASIA, LONDON и NY. Остальные сессии диапазоны копят,
                // но пулов не образуют — это осознанное ограничение объёма фазы 2.
                return null;
        }
    }

    private LiquidityPool AddPool(PoolType type, double price, Timeframe tf, DateTime createdAt, int memberCount = 1)
    {
        var pool = new LiquidityPool(_nextPoolId++, type, price, tf, createdAt, memberCount);
        _pools.Add(pool);
        return pool;
    }

    private void RememberSwing(Timeframe tf, Swing swing)
    {
        var history = _swingHistory[(tf, swing.Side)];
        history.Add(swing);
        var excess = history.Count - (_settings.EqLookbackSwings * 2);
        if (excess > 0)
        {
            history.RemoveRange(0, excess);
        }
    }

    private LiquidityPool? TryBuildEqualPool(Timeframe tf, Swing swing)
    {
        var atr = _atr[tf].Value;
        if (double.IsNaN(atr) || atr <= 0)
        {
            return null;
        }

        var tolerance = atr * _settings.EqToleranceAtr;
        var history = _swingHistory[(tf, swing.Side)];
        var from = Math.Max(0, history.Count - _settings.EqLookbackSwings);

        var members = 1;
        var extreme = swing.Price;
        for (var i = from; i < history.Count; i++)
        {
            var other = history[i];
            if (Math.Abs(other.Price - swing.Price) > tolerance)
            {
                continue;
            }

            members++;
            if (swing.Side == PoolSide.High ? other.Price > extreme : other.Price < extreme)
            {
                extreme = other.Price;
            }
        }

        if (members < 2)
        {
            return null;
        }

        var type = swing.Side == PoolSide.High ? PoolType.EQH : PoolType.EQL;
        foreach (var pool in _pools)
        {
            if (pool.Type == type && pool.Timeframe == tf && !pool.IsSwept && Math.Abs(pool.Price - extreme) <= tolerance)
            {
                // Кластер уже отмечен пулом на этом уровне — второй такой же не нужен.
                return null;
            }
        }

        return AddPool(type, extreme, tf, swing.ConfirmedAt, members);
    }

    private IReadOnlyList<LiquidityPool> HarvestSessionPools(SessionState session)
    {
        List<LiquidityPool>? created = null;
        foreach (var range in session.Previous.Values)
        {
            created = HarvestRange(range, created);
        }

        foreach (var range in session.Current.Values)
        {
            created = HarvestRange(range, created);
        }

        return (IReadOnlyList<LiquidityPool>?)created ?? Array.Empty<LiquidityPool>();
    }

    private List<LiquidityPool>? HarvestRange(SessionRange range, List<LiquidityPool>? created)
    {
        if (!range.IsComplete || !range.HasData || !_sessionRangesSeen.Add(range.Window.Key))
        {
            return created;
        }

        var high = SessionPoolType(range.Tag, PoolSide.High);
        var low = SessionPoolType(range.Tag, PoolSide.Low);
        if (high is null || low is null)
        {
            return created;
        }

        created ??= new List<LiquidityPool>();
        created.Add(AddPool(high.Value, range.High, Timeframe.D1, range.Window.EndUtc));
        created.Add(AddPool(low.Value, range.Low, Timeframe.D1, range.Window.EndUtc));
        return created;
    }

    /// <summary>Двигает окна возврата открытых событий. Разрешившиеся складывает в resolved (в порядке возникновения).</summary>
    private void AdvancePending(Bar bar, List<SweepEvent> resolved)
    {
        for (var i = 0; i < _pending.Count; i++)
        {
            if (_pending[i].Advance(bar))
            {
                resolved.Add(_pending[i]);
            }
        }

        _pending.RemoveAll(e => e.IsResolved);
    }

    private IReadOnlyList<SweepEvent> DetectSweeps(Bar bar, SessionTag session, List<SweepEvent> resolved)
    {
        List<SweepEvent>? swept = null;
        var atr = DistanceAtr;

        foreach (var pool in _pools)
        {
            if (!pool.IsActiveAt(bar.OpenTimeUtc) || !pool.IsPiercedBy(bar))
            {
                continue;
            }

            pool.MarkSwept(bar, atr);
            var sweep = new SweepEvent(pool, bar, session, atr, _settings.ReclaimWithinBars);
            (swept ??= new List<SweepEvent>()).Add(sweep);

            // Бар свипа — это бар 0 окна возврата: WICK-свип разрешается сразу.
            if (sweep.Advance(bar))
            {
                resolved.Add(sweep);
            }
            else
            {
                _pending.Add(sweep);
            }
        }

        return (IReadOnlyList<SweepEvent>?)swept ?? Array.Empty<SweepEvent>();
    }

    private void Prune(DateTime utc)
    {
        var cutoff = utc.AddDays(-_settings.PoolRetentionDays);
        for (var i = _pools.Count - 1; i >= 0; i--)
        {
            if (_pools[i].CreatedAt < cutoff)
            {
                _pools.RemoveAt(i);
            }
        }
    }
}
