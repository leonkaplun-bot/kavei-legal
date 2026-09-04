using LionRegime.Core.Liquidity;
using LionRegime.Core.Market;
using Xunit;

namespace LionRegime.Core.Tests.Liquidity;

public class SwingDetectorTests
{
    private static readonly DateTime Start = L.Utc(2026, 4, 1, 0, 0);

    [Fact]
    public void Five_bar_fractal_confirms_only_after_both_wings_closed()
    {
        var detector = new SwingDetector(Timeframe.H1, 5);
        double[] highs = { 112, 115, 120, 114, 111 };

        for (var i = 0; i < 4; i++)
        {
            Assert.Empty(detector.OnBar(L.Bar(Start.AddHours(i), highs[i], highs[i] - 10)));
        }

        var confirmed = detector.OnBar(L.Bar(Start.AddHours(4), highs[4], highs[4] - 10));
        var swing = Assert.Single(confirmed.Where(s => s.Side == PoolSide.High));
        Assert.Equal(120, swing.Price);
        Assert.Equal(Start.AddHours(2), swing.OccurredAt);

        // Свинг становится известен только на закрытии последнего подтверждающего бара — это и есть
        // отсутствие lookahead: раньше 05:00 знать про экстремум 02:00 нельзя.
        Assert.Equal(Start.AddHours(5), swing.ConfirmedAt);
        Assert.True(swing.ConfirmedAt > swing.OccurredAt);
    }

    [Fact]
    public void Monotonic_series_has_no_swings()
    {
        var detector = new SwingDetector(Timeframe.H1, 5);
        for (var i = 0; i < 20; i++)
        {
            Assert.Empty(detector.OnBar(L.Bar(Start.AddHours(i), 100 + i, 90 + i)));
        }
    }

    [Fact]
    public void Equal_highs_are_not_swings_they_are_left_to_the_eq_cluster()
    {
        var detector = new SwingDetector(Timeframe.H1, 5);
        double[] highs = { 110, 120, 120, 120, 110 };
        for (var i = 0; i < 5; i++)
        {
            Assert.Empty(detector.OnBar(L.Bar(Start.AddHours(i), highs[i], highs[i] - 10)).Where(s => s.Side == PoolSide.High));
        }
    }

    [Fact]
    public void Detects_swing_low_as_well()
    {
        var detector = new SwingDetector(Timeframe.H1, 5);
        double[] lows = { 100, 98, 90, 97, 101 };
        IReadOnlyList<Swing> last = Array.Empty<Swing>();
        for (var i = 0; i < 5; i++)
        {
            last = detector.OnBar(L.Bar(Start.AddHours(i), lows[i] + 5, lows[i]));
        }

        var swing = Assert.Single(last.Where(s => s.Side == PoolSide.Low));
        Assert.Equal(90, swing.Price);
    }

    [Fact]
    public void Wider_window_needs_more_confirmation()
    {
        var detector = new SwingDetector(Timeframe.H4, 7);
        Assert.Equal(3, detector.Wing);
        double[] highs = { 110, 112, 115, 130, 114, 113, 111 };
        for (var i = 0; i < 6; i++)
        {
            Assert.Empty(detector.OnBar(L.Bar(Start.AddHours(4 * i), highs[i], highs[i] - 10)));
        }

        var swing = Assert.Single(detector.OnBar(L.Bar(Start.AddHours(24), highs[6], highs[6] - 10)).Where(s => s.Side == PoolSide.High));
        Assert.Equal(130, swing.Price);
        Assert.Equal(Timeframe.H4, swing.Timeframe);
    }

    [Fact]
    public void Rejects_even_or_tiny_periods()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new SwingDetector(Timeframe.H1, 4));
        Assert.Throws<ArgumentOutOfRangeException>(() => new SwingDetector(Timeframe.H1, 1));
    }
}
