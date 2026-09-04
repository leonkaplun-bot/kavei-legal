using LionRegime.Core.Liquidity;
using LionRegime.Core.Market;

namespace LionRegime.Core.Tests.Liquidity;

/// <summary>Хелперы тестов слоя 2.</summary>
internal static class L
{
    public static DateTime Utc(int y, int mo, int d, int h, int mi) => new(y, mo, d, h, mi, 0, DateTimeKind.Utc);

    /// <summary>Бар с открытием и закрытием посередине диапазона — TR всегда равен High-Low.</summary>
    public static Bar Bar(DateTime openTimeUtc, double high, double low)
    {
        var mid = (high + low) / 2.0;
        return new Bar(openTimeUtc, mid, high, low, mid);
    }

    public static Bar Bar(DateTime openTimeUtc, double high, double low, double close) =>
        new Bar(openTimeUtc, Math.Min(Math.Max((high + low) / 2.0, low), high), high, low, close);

    /// <summary>
    /// 14 одинаковых H1-баров с диапазоном atr → ATR(14, H1) ровно atr.
    /// Бары идентичны, поэтому ни одного фрактального свинга и ни одного пула они не создают.
    /// Возвращает время открытия следующего свободного H1-бара.
    /// </summary>
    public static DateTime WarmUpH1(LiquidityMap map, double atr = 10.0, double low = 100.0, DateTime? start = null)
    {
        var t = start ?? Utc(2026, 3, 31, 0, 0);
        for (var i = 0; i < 14; i++)
        {
            map.OnHigherTimeframeBar(Timeframe.H1, Bar(t, low + atr, low));
            t = t.AddHours(1);
        }

        return t;
    }

    /// <summary>
    /// Три пары пулов вокруг цены 100: PDH/PDL 110/90, PWH/PWL 130/70, PMH/PML 150/50.
    /// Все известны к 2026-04-01 00:00 UTC. ATR(14, H1) = 10.
    /// </summary>
    public static LiquidityMap FixtureAroundHundred(LiquidityMapSettings? settings = null)
    {
        var map = new LiquidityMap(settings);
        WarmUpH1(map);
        map.OnHigherTimeframeBar(Timeframe.MN1, Bar(Utc(2026, 2, 1, 0, 0), 150, 50));
        map.OnHigherTimeframeBar(Timeframe.W1, Bar(Utc(2026, 3, 23, 0, 0), 130, 70));
        map.OnHigherTimeframeBar(Timeframe.D1, Bar(Utc(2026, 3, 31, 0, 0), 110, 90));
        return map;
    }

    /// <summary>Нейтральный бар M5, который не задевает ни один пул фикстуры.</summary>
    public static void QuietM5(LiquidityMap map, DateTime at) => map.OnBar(Bar(at, 100.5, 99.5, 100.0));

    public static LiquidityPool Single(this IReadOnlyList<LiquidityPool> pools, PoolType type) =>
        pools.Single(p => p.Type == type);
}
