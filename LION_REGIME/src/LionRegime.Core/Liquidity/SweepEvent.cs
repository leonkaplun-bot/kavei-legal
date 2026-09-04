using System;
using System.Globalization;
using LionRegime.Core.Market;

namespace LionRegime.Core.Liquidity;

/// <summary>
/// Событие снятия пула. Главный вход стратегий разворота и вход детектора режима DISTRIBUTION.
///
/// Внимание на время: тип свипа и глубина известны сразу, а возврат (Reclaimed) — только через
/// ReclaimWithinBars баров. Пока окно не закрылось, IsResolved = false и Reclaimed = null.
/// Таггер обязан писать колонку sweep_reclaimed вторым проходом, иначе это lookahead.
/// </summary>
public sealed class SweepEvent
{
    private readonly int _reclaimWithinBars;
    private int _barsSinceSweep;

    internal SweepEvent(LiquidityPool pool, Bar bar, Sessions.SessionTag session, double atr, int reclaimWithinBars)
    {
        Pool = pool ?? throw new ArgumentNullException(nameof(pool));
        SweptAt = bar.OpenTimeUtc;
        Session = session;
        Type = pool.SweepType ?? throw new InvalidOperationException("Pool must be marked swept before the event is created");
        DepthAtr = pool.SweepDepthAtr;
        Atr = atr;
        _reclaimWithinBars = reclaimWithinBars;
    }

    public LiquidityPool Pool { get; }

    public PoolType PoolType => Pool.Type;

    public DateTime SweptAt { get; }

    /// <summary>Сессия, в которой произошёл свип. Половина научного вопроса фазы 2.</summary>
    public Sessions.SessionTag Session { get; }

    public SweepType Type { get; }

    public double DepthAtr { get; }

    /// <summary>ATR, которым мерили глубину. NaN, если ATR не был готов.</summary>
    public double Atr { get; }

    /// <summary>null, пока окно возврата не закрылось.</summary>
    public bool? Reclaimed { get; private set; }

    public bool IsResolved => Reclaimed.HasValue;

    /// <summary>На каком баре после свипа случился возврат. 0 = на самом баре свипа (это всегда WICK).</summary>
    public int? ReclaimedAtBar { get; private set; }

    /// <summary>
    /// Прогоняет очередной бар через окно возврата. Возвращает true, когда событие окончательно разрешилось.
    /// Бар свипа тоже проходит через эту проверку как бар 0.
    /// </summary>
    internal bool Advance(Bar bar)
    {
        if (IsResolved)
        {
            return true;
        }

        if (Pool.IsReclaimedBy(bar))
        {
            Reclaimed = true;
            ReclaimedAtBar = _barsSinceSweep;
            Pool.SetReclaimed(true);
            return true;
        }

        if (_barsSinceSweep >= _reclaimWithinBars)
        {
            Reclaimed = false;
            Pool.SetReclaimed(false);
            return true;
        }

        _barsSinceSweep++;
        return false;
    }

    public override string ToString() =>
        string.Format(
            CultureInfo.InvariantCulture,
            "{0:yyyy-MM-dd HH:mm}Z {1} {2} {3} depth={4:F2}ATR reclaimed={5}",
            SweptAt,
            Session,
            PoolType,
            Type,
            DepthAtr,
            Reclaimed?.ToString() ?? "pending");
}
