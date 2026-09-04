using LionRegime.Core.Liquidity;
using Xunit;

namespace LionRegime.Core.Tests.Liquidity;

/// <summary>
/// Главный тест слоя 2.
///
/// Известный failure mode прошлого бота: тейк ставился на БЛИЖНЮЮ ликвидность вместо ДАЛЬНЕЙ,
/// и это инвертировало весь edge. Здесь это зафиксировано тестами: Near — ближайший уровень,
/// Far — самый дальний в пределах лимита. Для long Far = максимальная цена, для short — минимальная.
/// </summary>
public class GetTargetsTests
{
    private const double Price = 100.0;

    private static LiquidityMap Ready(LiquidityMapSettings? settings = null)
    {
        var map = L.FixtureAroundHundred(settings);
        L.QuietM5(map, L.Utc(2026, 4, 1, 7, 0));
        return map;
    }

    [Fact]
    public void Long_near_is_the_closest_pool_and_far_is_the_highest()
    {
        var targets = Ready().GetTargets(TradeDirection.Long, Price);

        Assert.Equal(3, targets.Count);
        Assert.Equal(new[] { 110.0, 130.0, 150.0 }, targets.Pools.Select(p => p.Price).ToArray());
        Assert.Equal(PoolType.PDH, targets.Near!.Type);
        Assert.Equal(110.0, targets.Near.Price);
        Assert.Equal(PoolType.PMH, targets.Far!.Type);
        Assert.Equal(150.0, targets.Far.Price);

        // Far обязан быть максимумом по цене — это и есть array.max-логика из ТЗ.
        Assert.Equal(targets.Pools.Max(p => p.Price), targets.Far.Price);
    }

    [Fact]
    public void Short_near_is_the_closest_pool_and_far_is_the_lowest()
    {
        var targets = Ready().GetTargets(TradeDirection.Short, Price);

        Assert.Equal(3, targets.Count);
        Assert.Equal(new[] { 90.0, 70.0, 50.0 }, targets.Pools.Select(p => p.Price).ToArray());
        Assert.Equal(PoolType.PDL, targets.Near!.Type);
        Assert.Equal(90.0, targets.Near.Price);
        Assert.Equal(PoolType.PML, targets.Far!.Type);
        Assert.Equal(50.0, targets.Far.Price);

        // Для short Far — это минимум, array.min-логика из ТЗ.
        Assert.Equal(targets.Pools.Min(p => p.Price), targets.Far.Price);
    }

    [Fact]
    public void Far_is_never_the_same_as_near_when_several_pools_exist()
    {
        // Регрессия на failure mode прошлого бота: если эти двое совпали при 3 пулах — TP уехал на ближний уровень.
        foreach (var direction in new[] { TradeDirection.Long, TradeDirection.Short })
        {
            var targets = Ready().GetTargets(direction, Price);
            Assert.True(targets.Count > 1);
            Assert.NotSame(targets.Near, targets.Far);
            Assert.True(
                targets.DistanceAtr(targets.Far!) > targets.DistanceAtr(targets.Near!),
                $"{direction}: far must be strictly farther than near");
        }
    }

    [Fact]
    public void Distances_are_measured_in_h1_atr()
    {
        var targets = Ready().GetTargets(TradeDirection.Long, Price);
        Assert.Equal(10.0, targets.Atr, 10);
        Assert.Equal(1.0, targets.DistanceAtr(targets.Near!), 10);   // 110 - 100 = 10 = 1 ATR
        Assert.Equal(5.0, targets.DistanceAtr(targets.Far!), 10);    // 150 - 100 = 50 = 5 ATR
    }

    [Fact]
    public void Pools_beyond_max_distance_are_dropped()
    {
        var map = Ready(new LiquidityMapSettings { MaxDistanceAtr = 2.5 }); // 2.5 × 10 = 25
        var targets = map.GetTargets(TradeDirection.Long, Price);

        Assert.Single(targets.Pools);
        Assert.Equal(110.0, targets.Far!.Price);
        Assert.Same(targets.Near, targets.Far);
    }

    [Fact]
    public void Swept_pools_stop_being_targets()
    {
        var map = Ready();
        map.OnBar(L.Bar(L.Utc(2026, 4, 1, 7, 5), 111, 99, 105)); // снимает PDH 110

        var targets = map.GetTargets(TradeDirection.Long, Price);
        Assert.Equal(2, targets.Count);
        Assert.Equal(130.0, targets.Near!.Price);
        Assert.Equal(150.0, targets.Far!.Price);
        Assert.DoesNotContain(targets.Pools, p => p.Type == PoolType.PDH);
    }

    [Fact]
    public void Pools_exactly_at_price_or_on_the_wrong_side_are_excluded()
    {
        var map = Ready();
        Assert.DoesNotContain(map.GetTargets(TradeDirection.Long, 110.0).Pools, p => p.Price <= 110.0);
        Assert.DoesNotContain(map.GetTargets(TradeDirection.Short, 90.0).Pools, p => p.Price >= 90.0);
    }

    [Fact]
    public void Empty_when_nothing_lies_in_that_direction()
    {
        var map = Ready();
        var above = map.GetTargets(TradeDirection.Long, 1000.0);
        Assert.True(above.IsEmpty);
        Assert.Null(above.Near);
        Assert.Null(above.Far);
    }

    [Fact]
    public void Can_be_restricted_to_pool_types()
    {
        var targets = Ready().GetTargets(TradeDirection.Long, Price, onlyTypes: new[] { PoolType.PWH, PoolType.PMH });
        Assert.Equal(new[] { PoolType.PWH, PoolType.PMH }, targets.Pools.Select(p => p.Type).ToArray());
        Assert.Equal(130.0, targets.Near!.Price);
        Assert.Equal(150.0, targets.Far!.Price);
    }

    [Fact]
    public void Without_atr_the_distance_filter_is_disabled_rather_than_dropping_everything()
    {
        var map = new LiquidityMap();
        map.OnHigherTimeframeBar(LionRegime.Core.Market.Timeframe.D1, L.Bar(L.Utc(2026, 3, 31, 0, 0), 110, 90));
        L.QuietM5(map, L.Utc(2026, 4, 1, 7, 0));

        var targets = map.GetTargets(TradeDirection.Long, Price);
        Assert.True(double.IsNaN(map.DistanceAtr));
        Assert.Single(targets.Pools);
        Assert.True(double.IsNaN(targets.DistanceAtr(targets.Far!)));
    }

    [Fact]
    public void Nan_price_is_rejected()
    {
        Assert.Throws<ArgumentException>(() => Ready().GetTargets(TradeDirection.Long, double.NaN));
    }
}
