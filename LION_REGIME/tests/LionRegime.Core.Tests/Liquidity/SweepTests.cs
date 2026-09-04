using LionRegime.Core.Liquidity;
using Xunit;

namespace LionRegime.Core.Tests.Liquidity;

/// <summary>
/// Свипы. Разделение WICK и BODY — открытый research-вопрос проекта: случай 11/06 был body-свипом,
/// текущее правило входа его отбрасывает, а он дал бы +26.8R. Разметка обязана различать их,
/// поэтому оба типа тестируются отдельно.
/// </summary>
public class SweepTests
{
    private static readonly DateTime T0 = L.Utc(2026, 4, 1, 7, 0);

    private static LiquidityMap Ready(LiquidityMapSettings? settings = null)
    {
        var map = L.FixtureAroundHundred(settings);
        L.QuietM5(map, T0);
        return map;
    }

    [Fact]
    public void Wick_sweep_closes_back_inside_and_reclaims_on_the_sweep_bar_itself()
    {
        var map = Ready();
        var update = map.OnBar(L.Bar(T0.AddMinutes(5), 112, 99, 108)); // прокол 110, закрытие ниже

        var sweep = Assert.Single(update.NewSweeps);
        Assert.Equal(PoolType.PDH, sweep.PoolType);
        Assert.Equal(SweepType.WICK, sweep.Type);
        Assert.Equal(0.2, sweep.DepthAtr, 10); // (112 - 110) / ATR 10
        Assert.True(sweep.IsResolved);
        Assert.True(sweep.Reclaimed);
        Assert.Equal(0, sweep.ReclaimedAtBar);
        Assert.Contains(sweep, update.ResolvedSweeps);
        Assert.Empty(map.PendingSweeps);
    }

    [Fact]
    public void Body_sweep_closes_beyond_the_level_and_stays_pending()
    {
        var map = Ready();
        var update = map.OnBar(L.Bar(T0.AddMinutes(5), 112, 105, 111)); // закрытие выше 110

        var sweep = Assert.Single(update.NewSweeps);
        Assert.Equal(SweepType.BODY, sweep.Type);
        Assert.False(sweep.IsResolved);
        Assert.Null(sweep.Reclaimed);
        Assert.Empty(update.ResolvedSweeps);
        Assert.Single(map.PendingSweeps);
    }

    [Fact]
    public void Body_sweep_reclaimed_inside_the_window_is_recorded_as_reclaimed()
    {
        var map = Ready();
        var swept = map.OnBar(L.Bar(T0.AddMinutes(5), 112, 105, 111)).NewSweeps.Single();

        map.OnBar(L.Bar(T0.AddMinutes(10), 112, 110.5, 111));
        map.OnBar(L.Bar(T0.AddMinutes(15), 112, 110.5, 111));
        var update = map.OnBar(L.Bar(T0.AddMinutes(20), 111, 105, 108)); // вернулись под 110

        Assert.Same(swept, Assert.Single(update.ResolvedSweeps));
        Assert.True(swept.Reclaimed);
        Assert.Equal(3, swept.ReclaimedAtBar);
        Assert.True(swept.Pool.ReclaimedWithinNBars);
    }

    [Fact]
    public void Body_sweep_that_never_comes_back_resolves_as_not_reclaimed()
    {
        var map = Ready();
        var swept = map.OnBar(L.Bar(T0.AddMinutes(5), 112, 105, 111)).NewSweeps.Single();

        // Окно возврата = бар свипа (0) плюс ReclaimWithinBars следующих баров.
        for (var i = 1; i <= map.Settings.ReclaimWithinBars - 1; i++)
        {
            var update = map.OnBar(L.Bar(T0.AddMinutes(5 + (5 * i)), 115, 111, 114));
            Assert.Empty(update.ResolvedSweeps);
            Assert.False(swept.IsResolved);
        }

        var last = map.OnBar(L.Bar(T0.AddMinutes(5 + (5 * map.Settings.ReclaimWithinBars)), 115, 111, 114));
        Assert.Same(swept, Assert.Single(last.ResolvedSweeps));
        Assert.False(swept.Reclaimed);
        Assert.False(swept.Pool.ReclaimedWithinNBars);
        Assert.Empty(map.PendingSweeps);
    }

    [Fact]
    public void Low_side_pool_is_swept_by_the_bar_low()
    {
        var map = Ready();
        var sweep = Assert.Single(map.OnBar(L.Bar(T0.AddMinutes(5), 101, 88, 92)).NewSweeps);

        Assert.Equal(PoolType.PDL, sweep.PoolType);
        Assert.Equal(SweepType.WICK, sweep.Type);   // закрытие 92 выше уровня 90
        Assert.Equal(0.2, sweep.DepthAtr, 10);      // (90 - 88) / ATR 10
        Assert.True(sweep.Reclaimed);
    }

    [Fact]
    public void One_bar_can_sweep_several_pools_at_once()
    {
        var map = Ready();
        var update = map.OnBar(L.Bar(T0.AddMinutes(5), 135, 99, 120)); // проходит 110 и 130

        Assert.Equal(2, update.NewSweeps.Count);
        Assert.Equal(new[] { PoolType.PDH, PoolType.PWH }, update.NewSweeps.Select(s => s.PoolType).OrderBy(t => t.ToString()).ToArray());

        // Один и тот же бар снимает два уровня по-разному, и это важно различать:
        // 110 остался под закрытием (BODY), а 130 проколот и отдан обратно (WICK).
        Assert.Equal(SweepType.BODY, update.NewSweeps.Single(s => s.PoolType == PoolType.PDH).Type);
        Assert.Equal(SweepType.WICK, update.NewSweeps.Single(s => s.PoolType == PoolType.PWH).Type);
        Assert.True(update.NewSweeps.Single(s => s.PoolType == PoolType.PWH).Reclaimed);
    }

    [Fact]
    public void Touching_the_level_without_going_through_it_is_not_a_sweep()
    {
        var map = Ready();
        Assert.Empty(map.OnBar(L.Bar(T0.AddMinutes(5), 110, 90, 100)).NewSweeps); // ровно по уровням
        Assert.False(map.Pools.Single(p => p.Type == PoolType.PDH).IsSwept);
    }

    [Fact]
    public void Sweep_carries_the_session_from_layer_one()
    {
        var map = Ready();
        var engine = new LionRegime.Core.Sessions.SessionEngine();
        var at = L.Utc(2026, 4, 1, 8, 0); // лето: 08:00 UTC = LONDON
        var state = engine.OnBar(at, 112, 99);

        var sweep = Assert.Single(map.OnBar(L.Bar(at, 112, 99, 108), state).NewSweeps);
        Assert.Equal(LionRegime.Core.Sessions.SessionTag.LONDON, sweep.Session);
    }

    [Fact]
    public void Depth_is_nan_while_atr_is_not_ready()
    {
        var map = new LiquidityMap();
        map.OnHigherTimeframeBar(LionRegime.Core.Market.Timeframe.D1, L.Bar(L.Utc(2026, 3, 31, 0, 0), 110, 90));
        var sweep = Assert.Single(map.OnBar(L.Bar(T0, 112, 99, 108)).NewSweeps);
        Assert.True(double.IsNaN(sweep.DepthAtr));
    }

    [Fact]
    public void A_pool_is_swept_at_most_once()
    {
        var map = Ready();
        map.OnBar(L.Bar(T0.AddMinutes(5), 112, 99, 108));
        Assert.Empty(map.OnBar(L.Bar(T0.AddMinutes(10), 115, 99, 108)).NewSweeps.Where(s => s.PoolType == PoolType.PDH));
    }
}
