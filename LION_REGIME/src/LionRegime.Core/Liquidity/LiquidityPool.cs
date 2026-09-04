using System;
using System.Globalization;
using LionRegime.Core.Market;

namespace LionRegime.Core.Liquidity;

/// <summary>
/// Пул ликвидности: цена, за которой стоят стопы. Пока не снят — потенциальная цель.
/// Создаётся только по ЗАКРЫТЫМ данным; CreatedAt — момент, когда пул стал известен.
/// Пул не может использоваться баром, у которого OpenTimeUtc &lt; CreatedAt. Это защита от lookahead.
/// </summary>
public sealed class LiquidityPool
{
    public LiquidityPool(long id, PoolType type, double price, Timeframe timeframe, DateTime createdAt, int memberCount = 1)
    {
        if (double.IsNaN(price))
        {
            throw new ArgumentException("Pool price must not be NaN", nameof(price));
        }

        if (memberCount < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(memberCount));
        }

        Id = id;
        Type = type;
        Side = PoolTypes.SideOf(type);
        Price = price;
        Timeframe = timeframe;
        CreatedAt = Sessions.TimeZones.EnsureUtc(createdAt);
        MemberCount = memberCount;
        SweepDepthAtr = double.NaN;
    }

    public long Id { get; }

    public PoolType Type { get; }

    public PoolSide Side { get; }

    public double Price { get; }

    /// <summary>Таймфрейм источника. Сессионные пулы помечаются D1: это уровни дневного масштаба.</summary>
    public Timeframe Timeframe { get; }

    /// <summary>Момент, когда пул стал известен (закрытие породившего бара или конец сессии).</summary>
    public DateTime CreatedAt { get; }

    /// <summary>Сколько свингов вошло в кластер. Для EQH/EQL >= 2, для остальных 1.</summary>
    public int MemberCount { get; }

    public bool IsSwept { get; private set; }

    public DateTime? SweptAt { get; private set; }

    public SweepType? SweepType { get; private set; }

    /// <summary>На сколько ATR ушли за уровень. NaN, если ATR ещё не готов.</summary>
    public double SweepDepthAtr { get; private set; }

    /// <summary>
    /// Вернулась ли цена обратно за уровень в окне возврата.
    /// null — свипа не было, либо окно ещё не закрылось (значение станет известно позже).
    /// Писать это в CSV на баре свипа нельзя: это был бы lookahead.
    /// </summary>
    public bool? ReclaimedWithinNBars { get; private set; }

    /// <summary>Активен ли пул на момент времени: уже известен и ещё не снят.</summary>
    public bool IsActiveAt(DateTime utc) => !IsSwept && CreatedAt <= Sessions.TimeZones.EnsureUtc(utc);

    /// <summary>Пробит ли уровень этим баром (по экстремуму, строго за уровень).</summary>
    public bool IsPiercedBy(Bar bar) =>
        Side == PoolSide.High ? bar.High > Price : bar.Low < Price;

    /// <summary>Закрылся ли бар обратно ЗА уровнем — это и есть возврат (reclaim).</summary>
    public bool IsReclaimedBy(Bar bar) =>
        Side == PoolSide.High ? bar.Close < Price : bar.Close > Price;

    internal void MarkSwept(Bar bar, double atr)
    {
        if (IsSwept)
        {
            throw new InvalidOperationException($"Pool {Id} ({Type} @ {Price}) is already swept");
        }

        IsSwept = true;
        SweptAt = bar.OpenTimeUtc;
        SweepType = IsReclaimedBy(bar) ? Liquidity.SweepType.WICK : Liquidity.SweepType.BODY;
        var depth = Side == PoolSide.High ? bar.High - Price : Price - bar.Low;
        SweepDepthAtr = atr > 0 && !double.IsNaN(atr) ? depth / atr : double.NaN;
    }

    internal void SetReclaimed(bool reclaimed) => ReclaimedWithinNBars = reclaimed;

    public override string ToString() =>
        string.Format(CultureInfo.InvariantCulture, "{0} {1} @{2}{3}", Type, Timeframe, Price, IsSwept ? " swept" : string.Empty);
}
