using LionRegime.Core.Indicators;
using LionRegime.Core.Tests.Liquidity;
using Xunit;

namespace LionRegime.Core.Tests.Indicators;

public class AtrCalculatorTests
{
    [Fact]
    public void Not_ready_until_period_bars_arrived()
    {
        var atr = new AtrCalculator(14);
        var t = L.Utc(2026, 4, 1, 0, 0);
        for (var i = 0; i < 13; i++)
        {
            atr.OnBar(L.Bar(t.AddHours(i), 101, 100));
            Assert.False(atr.IsReady);
            Assert.True(double.IsNaN(atr.Value));
        }

        atr.OnBar(L.Bar(t.AddHours(13), 101, 100));
        Assert.True(atr.IsReady);
        Assert.Equal(1.0, atr.Value, 10);
        Assert.Equal(14, atr.BarsProcessed);
    }

    [Fact]
    public void Wilder_smoothing_after_the_seed()
    {
        var atr = new AtrCalculator(14);
        var t = L.Utc(2026, 4, 1, 0, 0);
        for (var i = 0; i < 14; i++)
        {
            atr.OnBar(L.Bar(t.AddHours(i), 101, 100));
        }

        Assert.Equal(1.0, atr.Value, 10);

        // TR = 15 на 15-м баре: ATR = (1.0 * 13 + 15) / 14 = 2.0
        atr.OnBar(L.Bar(t.AddHours(14), 115, 100));
        Assert.Equal(2.0, atr.Value, 10);
    }

    [Fact]
    public void True_range_accounts_for_the_gap_from_previous_close()
    {
        var atr = new AtrCalculator(1);
        var t = L.Utc(2026, 4, 1, 0, 0);
        atr.OnBar(L.Bar(t, 101, 100));                      // TR = 1, close = 100.5
        var value = atr.OnBar(L.Bar(t.AddHours(1), 110, 109)); // гэп вверх: TR = 110 - 100.5 = 9.5
        Assert.Equal(9.5, value, 10);
    }

    [Fact]
    public void Rejects_non_positive_period()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new AtrCalculator(0));
        Assert.Throws<ArgumentOutOfRangeException>(() => new AtrCalculator(-1));
    }
}
