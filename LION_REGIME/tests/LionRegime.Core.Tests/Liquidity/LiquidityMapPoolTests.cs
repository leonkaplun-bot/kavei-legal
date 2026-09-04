using LionRegime.Core.Liquidity;
using LionRegime.Core.Market;
using LionRegime.Core.Sessions;
using Xunit;

namespace LionRegime.Core.Tests.Liquidity;

public class LiquidityMapPoolTests
{
    [Fact]
    public void Daily_weekly_and_monthly_bars_create_their_pools_at_their_close_time()
    {
        var map = L.FixtureAroundHundred();

        Assert.Equal(110.0, map.Pools.Single(PoolType.PDH).Price);
        Assert.Equal(90.0, map.Pools.Single(PoolType.PDL).Price);
        Assert.Equal(130.0, map.Pools.Single(PoolType.PWH).Price);
        Assert.Equal(70.0, map.Pools.Single(PoolType.PWL).Price);
        Assert.Equal(150.0, map.Pools.Single(PoolType.PMH).Price);
        Assert.Equal(50.0, map.Pools.Single(PoolType.PML).Price);

        Assert.Equal(L.Utc(2026, 4, 1, 0, 0), map.Pools.Single(PoolType.PDH).CreatedAt);
        Assert.Equal(L.Utc(2026, 3, 30, 0, 0), map.Pools.Single(PoolType.PWH).CreatedAt);
        Assert.Equal(L.Utc(2026, 3, 1, 0, 0), map.Pools.Single(PoolType.PMH).CreatedAt);
        Assert.Equal(Timeframe.D1, map.Pools.Single(PoolType.PDH).Timeframe);
    }

    [Fact]
    public void Session_range_becomes_a_pool_only_once_the_session_is_over()
    {
        var engine = new SessionEngine();
        var map = new LiquidityMap();

        // ASIA 01.04 лето: 31.03 23:00 → 01.04 07:00 UTC. Плоские бары: H = 101, L = 99.
        LiquidityUpdate? closing = null;
        for (var t = L.Utc(2026, 3, 31, 23, 0); t < L.Utc(2026, 4, 1, 7, 0); t = t.AddMinutes(5))
        {
            var state = engine.OnBar(t, 101, 99);
            var update = map.OnBar(L.Bar(t, 101, 99, 100), state);
            Assert.Empty(update.NewPools); // пока Азия идёт — пула нет
        }

        var at = L.Utc(2026, 4, 1, 7, 0);
        closing = map.OnBar(L.Bar(at, 100.5, 99.5, 100), engine.OnBar(at, 100.5, 99.5));

        Assert.Equal(2, closing.NewPools.Count);
        Assert.Equal(101.0, closing.NewPools.Single(PoolType.ASIA_H).Price);
        Assert.Equal(99.0, closing.NewPools.Single(PoolType.ASIA_L).Price);
        Assert.Equal(at, closing.NewPools.Single(PoolType.ASIA_H).CreatedAt);
    }

    [Fact]
    public void Session_pool_is_created_once_per_session_day()
    {
        var engine = new SessionEngine();
        var map = new LiquidityMap();
        var created = 0;

        for (var t = L.Utc(2026, 3, 31, 23, 0); t < L.Utc(2026, 4, 1, 12, 0); t = t.AddMinutes(5))
        {
            created += map.OnBar(L.Bar(t, 101, 99, 100), engine.OnBar(t, 101, 99)).NewPools.Count;
        }

        // За этот отрезок завершились ASIA (07:00) и LONDON (11:30) — по паре пулов на каждую.
        Assert.Equal(4, created);
        Assert.Single(map.Pools.Where(p => p.Type == PoolType.ASIA_H));
        Assert.Single(map.Pools.Where(p => p.Type == PoolType.LONDON_H));
    }

    [Fact]
    public void Sessions_without_a_pool_type_are_skipped()
    {
        var engine = new SessionEngine();
        var map = new LiquidityMap();

        // Окно 11:35–13:35 лета: внутри целиком лежит только закрытие NY_PRE (13:30).
        for (var t = L.Utc(2026, 4, 1, 11, 35); t < L.Utc(2026, 4, 1, 13, 35); t = t.AddMinutes(5))
        {
            var state = engine.OnBar(t, 101, 99);
            map.OnBar(L.Bar(t, 101, 99, 100), state);
        }

        // NY_PRE завершился, но ТЗ определяет сессионные пулы только для ASIA, LONDON и NY_CASH.
        Assert.Empty(map.Pools);
    }

    [Fact]
    public void Confirmed_swings_become_pools_and_equal_highs_form_a_cluster()
    {
        var map = new LiquidityMap();
        var t = L.WarmUpH1(map);
        double[,] series =
        {
            { 112, 102 }, { 115, 105 }, { 120, 110 }, { 114, 104 }, { 111, 101 },
            { 113, 103 }, { 116, 106 }, { 120.5, 110.5 }, { 115, 105 }, { 112, 102 },
        };

        for (var i = 0; i < series.GetLength(0); i++)
        {
            map.OnHigherTimeframeBar(Timeframe.H1, L.Bar(t.AddHours(i), series[i, 0], series[i, 1]));
        }

        var swingHighs = map.Pools.Where(p => p.Type == PoolType.SWING_H).ToList();
        Assert.Equal(new[] { 120.0, 120.5 }, swingHighs.Select(p => p.Price).ToArray());
        Assert.All(swingHighs, p => Assert.Equal(Timeframe.H1, p.Timeframe));

        // 120 и 120.5 отличаются на 0.5 при допуске 0.15 × ATR(10) = 1.5 → равные хаи.
        var eq = Assert.Single(map.Pools.Where(p => p.Type == PoolType.EQH));
        Assert.Equal(120.5, eq.Price); // уровень берётся по максимуму кластера — там стоят стопы
        Assert.Equal(2, eq.MemberCount);
    }

    [Fact]
    public void Far_apart_swings_do_not_form_an_equal_cluster()
    {
        var map = new LiquidityMap();
        var t = L.WarmUpH1(map);
        double[,] series =
        {
            { 112, 102 }, { 115, 105 }, { 120, 110 }, { 114, 104 }, { 111, 101 },
            { 113, 103 }, { 116, 106 }, { 125, 115 }, { 115, 105 }, { 112, 102 },
        };

        for (var i = 0; i < series.GetLength(0); i++)
        {
            map.OnHigherTimeframeBar(Timeframe.H1, L.Bar(t.AddHours(i), series[i, 0], series[i, 1]));
        }

        Assert.Equal(2, map.Pools.Count(p => p.Type == PoolType.SWING_H)); // 120 и 125 разошлись больше чем на 1.5
        Assert.Empty(map.Pools.Where(p => p.Type == PoolType.EQH));
    }

    [Fact]
    public void Swing_pool_is_created_at_confirmation_time_not_at_the_extreme()
    {
        var map = new LiquidityMap();
        var t = L.WarmUpH1(map);
        double[,] series = { { 112, 102 }, { 115, 105 }, { 120, 110 }, { 114, 104 }, { 111, 101 } };
        for (var i = 0; i < 5; i++)
        {
            map.OnHigherTimeframeBar(Timeframe.H1, L.Bar(t.AddHours(i), series[i, 0], series[i, 1]));
        }

        var swing = map.Pools.Single(PoolType.SWING_H);
        Assert.Equal(t.AddHours(5), swing.CreatedAt);  // закрытие пятого бара, а не второго
    }

    [Fact]
    public void Higher_timeframe_bars_must_be_chronological()
    {
        var map = new LiquidityMap();
        map.OnHigherTimeframeBar(Timeframe.D1, L.Bar(L.Utc(2026, 3, 31, 0, 0), 110, 90));
        Assert.Throws<InvalidOperationException>(() =>
            map.OnHigherTimeframeBar(Timeframe.D1, L.Bar(L.Utc(2026, 3, 31, 0, 0), 110, 90)));
        Assert.Throws<InvalidOperationException>(() =>
            map.OnHigherTimeframeBar(Timeframe.D1, L.Bar(L.Utc(2026, 3, 30, 0, 0), 110, 90)));
        Assert.Throws<ArgumentException>(() =>
            map.OnHigherTimeframeBar(Timeframe.M5, L.Bar(L.Utc(2026, 4, 1, 0, 0), 110, 90)));
    }

    [Fact]
    public void Settings_are_validated()
    {
        Assert.Throws<InvalidOperationException>(() => new LiquidityMap(new LiquidityMapSettings { SwingPeriod = 4 }));
        Assert.Throws<InvalidOperationException>(() => new LiquidityMap(new LiquidityMapSettings { MaxDistanceAtr = 0 }));
        Assert.Throws<InvalidOperationException>(() => new LiquidityMap(new LiquidityMapSettings { EqToleranceAtr = -1 }));
    }
}
