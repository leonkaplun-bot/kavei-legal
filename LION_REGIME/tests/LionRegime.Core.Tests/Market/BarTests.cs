using LionRegime.Core.Market;
using LionRegime.Core.Tests.Liquidity;
using Xunit;

namespace LionRegime.Core.Tests.Market;

public class BarTests
{
    [Fact]
    public void Rejects_impossible_bars()
    {
        var t = L.Utc(2026, 4, 1, 0, 0);
        Assert.Throws<ArgumentException>(() => new Bar(t, 100, 99, 101, 100));   // low > high
        Assert.Throws<ArgumentException>(() => new Bar(t, 105, 101, 99, 100));   // open вне диапазона
        Assert.Throws<ArgumentException>(() => new Bar(t, 100, 101, 99, 105));   // close вне диапазона
        Assert.Throws<ArgumentException>(() => new Bar(t, double.NaN, 101, 99, 100));
    }

    [Fact]
    public void Unspecified_kind_is_treated_as_utc()
    {
        var unspecified = new DateTime(2026, 4, 1, 7, 0, 0, DateTimeKind.Unspecified);
        var bar = new Bar(unspecified, 100, 101, 99, 100);
        Assert.Equal(DateTimeKind.Utc, bar.OpenTimeUtc.Kind);
    }

    [Theory]
    [InlineData(Timeframe.M5, 2026, 4, 1, 7, 0, 2026, 4, 1, 7, 5)]
    [InlineData(Timeframe.H1, 2026, 4, 1, 7, 0, 2026, 4, 1, 8, 0)]
    [InlineData(Timeframe.H4, 2026, 4, 1, 4, 0, 2026, 4, 1, 8, 0)]
    [InlineData(Timeframe.D1, 2026, 3, 31, 0, 0, 2026, 4, 1, 0, 0)]
    [InlineData(Timeframe.W1, 2026, 3, 23, 0, 0, 2026, 3, 30, 0, 0)]
    [InlineData(Timeframe.MN1, 2026, 2, 1, 0, 0, 2026, 3, 1, 0, 0)]
    [InlineData(Timeframe.MN1, 2026, 12, 1, 0, 0, 2027, 1, 1, 0, 0)]
    public void Close_time_of_each_timeframe(Timeframe tf, int y, int mo, int d, int h, int mi, int ey, int emo, int ed, int eh, int emi)
    {
        Assert.Equal(L.Utc(ey, emo, ed, eh, emi), Timeframes.CloseTimeOf(tf, L.Utc(y, mo, d, h, mi)));
    }
}
