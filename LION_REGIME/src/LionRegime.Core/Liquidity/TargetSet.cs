using System;
using System.Collections.Generic;
using System.Globalization;

namespace LionRegime.Core.Liquidity;

/// <summary>
/// Результат GetTargets: несобранные пулы в одну сторону, отсортированные по расстоянию.
///
/// ГЛАВНЫЙ УРОК ПРОШЛОГО БОТА: тейк ставится на Far, не на Near.
/// Near — уровень, о который нас стопят по дороге. Far — то, за чем рынок реально идёт.
/// Постановка TP на Near инвертировала весь edge предыдущей версии.
/// </summary>
public sealed class TargetSet
{
    public static readonly TargetSet Empty = new TargetSet(TradeDirection.Long, double.NaN, double.NaN, Array.Empty<LiquidityPool>());

    public TargetSet(TradeDirection direction, double fromPrice, double atr, IReadOnlyList<LiquidityPool> pools)
    {
        Direction = direction;
        FromPrice = fromPrice;
        Atr = atr;
        Pools = pools ?? throw new ArgumentNullException(nameof(pools));
    }

    public TradeDirection Direction { get; }

    public double FromPrice { get; }

    public double Atr { get; }

    /// <summary>По возрастанию расстояния от FromPrice.</summary>
    public IReadOnlyList<LiquidityPool> Pools { get; }

    public bool IsEmpty => Pools.Count == 0;

    public int Count => Pools.Count;

    /// <summary>Ближайший несобранный пул. Здесь нас стопят. Не цель.</summary>
    public LiquidityPool? Near => Pools.Count > 0 ? Pools[0] : null;

    /// <summary>
    /// Самый дальний пул в пределах maxDistanceAtr. ЭТО ЦЕЛЬ.
    /// Для long — максимальная цена среди пулов выше, для short — минимальная среди пулов ниже.
    /// </summary>
    public LiquidityPool? Far => Pools.Count > 0 ? Pools[Pools.Count - 1] : null;

    public double DistanceAtr(LiquidityPool pool)
    {
        if (pool is null)
        {
            throw new ArgumentNullException(nameof(pool));
        }

        return Atr > 0 && !double.IsNaN(Atr) ? Math.Abs(pool.Price - FromPrice) / Atr : double.NaN;
    }

    public override string ToString() =>
        Pools.Count == 0
            ? string.Format(CultureInfo.InvariantCulture, "{0}: no targets", Direction)
            : string.Format(CultureInfo.InvariantCulture, "{0}: near {1}, far {2} ({3} pools)", Direction, Near, Far, Pools.Count);
}
