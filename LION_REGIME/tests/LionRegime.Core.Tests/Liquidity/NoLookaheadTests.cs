using LionRegime.Core.Liquidity;
using LionRegime.Core.Market;
using LionRegime.Core.Sessions;
using Xunit;

namespace LionRegime.Core.Tests.Liquidity;

/// <summary>
/// Железное правило ТЗ: lookahead запрещён везде. Пул не существует для бара, который закрылся
/// раньше, чем пул стал известен — даже если данные старшего ТФ уже поданы в карту.
/// </summary>
public class NoLookaheadTests
{
    [Fact]
    public void A_daily_pool_cannot_be_swept_by_a_bar_that_closed_before_the_day_ended()
    {
        var map = new LiquidityMap();
        L.WarmUpH1(map);
        map.OnHigherTimeframeBar(Timeframe.D1, L.Bar(L.Utc(2026, 3, 31, 0, 0), 110, 90)); // известен с 01.04 00:00

        // Бар внутри тех же суток проходит 110 — но пула для него ещё не существует.
        var inside = map.OnBar(L.Bar(L.Utc(2026, 3, 31, 12, 0), 115, 99, 114));
        Assert.Empty(inside.NewSweeps);
        Assert.False(map.Pools.Single(PoolType.PDH).IsSwept);
        Assert.Empty(map.GetTargets(TradeDirection.Long, 100.0).Pools);

        // Следующие сутки — тот же уровень снимается.
        var after = map.OnBar(L.Bar(L.Utc(2026, 4, 1, 8, 0), 115, 99, 114));
        Assert.Single(after.NewSweeps);
        Assert.Equal(PoolType.PDH, after.NewSweeps[0].PoolType);
    }

    [Fact]
    public void Targets_asked_for_an_earlier_moment_ignore_later_pools()
    {
        var map = L.FixtureAroundHundred();
        L.QuietM5(map, L.Utc(2026, 4, 1, 7, 0));

        Assert.Equal(3, map.GetTargets(TradeDirection.Long, 100.0).Count);
        Assert.Equal(2, map.GetTargets(TradeDirection.Long, 100.0, asOf: L.Utc(2026, 3, 30, 12, 0)).Count); // без PDH
        Assert.Single(map.GetTargets(TradeDirection.Long, 100.0, asOf: L.Utc(2026, 3, 15, 0, 0)).Pools);    // только PMH
        Assert.Empty(map.GetTargets(TradeDirection.Long, 100.0, asOf: L.Utc(2026, 2, 15, 0, 0)).Pools);
    }

    [Fact]
    public void M5_bars_must_be_chronological()
    {
        var map = L.FixtureAroundHundred();
        map.OnBar(L.Bar(L.Utc(2026, 4, 1, 7, 0), 101, 99, 100));
        Assert.Throws<InvalidOperationException>(() => map.OnBar(L.Bar(L.Utc(2026, 4, 1, 7, 0), 101, 99, 100)));
        Assert.Throws<InvalidOperationException>(() => map.OnBar(L.Bar(L.Utc(2026, 4, 1, 6, 55), 101, 99, 100)));
    }

    [Fact]
    public void Session_state_must_belong_to_the_same_bar()
    {
        var map = new LiquidityMap();
        var engine = new SessionEngine();
        var state = engine.OnBar(L.Utc(2026, 4, 1, 8, 0), 101, 99);
        Assert.Throws<ArgumentException>(() => map.OnBar(L.Bar(L.Utc(2026, 4, 1, 8, 5), 101, 99, 100), state));
    }

    [Fact]
    public void Six_months_of_m5_bars_run_without_throwing()
    {
        var map = new LiquidityMap();
        var engine = new SessionEngine();
        var random = new Random(20260904);
        var price = 100.0;
        var bars = 0;
        var sweeps = 0;
        var nextH1 = L.Utc(2026, 3, 1, 0, 0);
        var nextD1 = L.Utc(2026, 3, 1, 0, 0);
        double h1High = double.MinValue, h1Low = double.MaxValue, d1High = double.MinValue, d1Low = double.MaxValue;

        for (var t = L.Utc(2026, 3, 1, 0, 0); t < L.Utc(2026, 9, 1, 0, 0); t = t.AddMinutes(5))
        {
            price += (random.NextDouble() - 0.5) * 0.4;
            var high = price + (random.NextDouble() * 0.3);
            var low = price - (random.NextDouble() * 0.3);
            h1High = Math.Max(h1High, high);
            h1Low = Math.Min(h1Low, low);
            d1High = Math.Max(d1High, high);
            d1Low = Math.Min(d1Low, low);

            if (t >= nextH1.AddHours(1))
            {
                map.OnHigherTimeframeBar(Timeframe.H1, L.Bar(nextH1, h1High, h1Low));
                nextH1 = nextH1.AddHours(1);
                h1High = double.MinValue;
                h1Low = double.MaxValue;
            }

            if (t >= nextD1.AddDays(1))
            {
                map.OnHigherTimeframeBar(Timeframe.D1, L.Bar(nextD1, d1High, d1Low));
                nextD1 = nextD1.AddDays(1);
                d1High = double.MinValue;
                d1Low = double.MaxValue;
            }

            sweeps += map.OnBar(L.Bar(t, high, low, price), engine.OnBar(t, high, low)).NewSweeps.Count;
            foreach (var direction in new[] { TradeDirection.Long, TradeDirection.Short })
            {
                var targets = map.GetTargets(direction, price);
                if (!targets.IsEmpty)
                {
                    var near = targets.DistanceAtr(targets.Near!);
                    var far = targets.DistanceAtr(targets.Far!);
                    Assert.True(double.IsNaN(far) || far >= near, "Far must never be closer than near");
                }
            }

            bars++;
        }

        Assert.Equal(184 * 288, bars); // 01.03–01.09.2026 = 184 дня по 288 баров M5
        Assert.True(sweeps > 100, $"expected a realistic number of sweeps, got {sweeps}");
        Assert.True(map.Pools.Count > 0);
    }
}
