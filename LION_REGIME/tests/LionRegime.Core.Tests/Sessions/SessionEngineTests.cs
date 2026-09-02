using LionRegime.Core.Calendar;
using LionRegime.Core.Sessions;
using Xunit;

namespace LionRegime.Core.Tests.Sessions;

public class SessionEngineTests
{
    private sealed class AlwaysHoliday : IHolidayCalendar
    {
        public bool IsHoliday(DateTime utc) => true;
    }

    /// <summary>Детерминированные бары: high растёт на 0.01 за бар, low = high - 0.5.</summary>
    private static (double High, double Low) Bar(int i) => (100.0 + i * 0.01, 100.0 + i * 0.01 - 0.5);

    private static List<SessionState> Feed(SessionEngine engine, DateTime fromUtc, DateTime toUtcExclusive)
    {
        var states = new List<SessionState>();
        var i = 0;
        for (var t = fromUtc; t < toUtcExclusive; t = t.AddMinutes(5), i++)
        {
            var (high, low) = Bar(i);
            states.Add(engine.OnBar(t, high, low));
        }

        return states;
    }

    [Fact]
    public void Asia_range_accumulates_only_its_own_bars()
    {
        var engine = new SessionEngine();
        // ASIA 01.04: 31.03 23:00 → 01.04 07:00 UTC = 96 баров. Кормим до 08:00, чтобы ASIA закрылась.
        var states = Feed(engine, T.Utc(2026, 3, 31, 23, 0), T.Utc(2026, 4, 1, 8, 0));

        var asia = states.Last().CurrentRange(SessionTag.ASIA)!;
        Assert.Equal(96, asia.BarCount);
        Assert.Equal(Bar(0).Low, asia.Low, 10);
        Assert.Equal(Bar(95).High, asia.High, 10);
        Assert.True(asia.IsComplete);
        Assert.Equal(T.Date(2026, 4, 1), asia.Window.AnchorLocalDate);

        // Первый бар ASIA: тег ASIA, открытие сессии, 0 минут.
        Assert.Equal(SessionTag.ASIA, states[0].Session);
        Assert.True(states[0].IsSessionOpen);
        Assert.Equal(0, states[0].MinutesIntoSession);
        Assert.Equal("2026-04-01 02:00", states[0].TimeIsrael.ToString("yyyy-MM-dd HH:mm"));
    }

    [Fact]
    public void Overlapping_bar_feeds_both_sessions_but_tag_is_highest_priority()
    {
        var engine = new SessionEngine();
        var states = Feed(engine, T.Utc(2026, 4, 1, 5, 55), T.Utc(2026, 4, 1, 7, 5));

        // 06:00–06:55 = 12 баров FRANKFURT, все они же входят в ASIA (05:55 + 12 = 13 баров ASIA).
        var last = states.Last();
        Assert.Equal(12, last.CurrentRange(SessionTag.FRANKFURT)!.BarCount);
        Assert.Equal(13, last.CurrentRange(SessionTag.ASIA)!.BarCount);
        Assert.Equal(SessionTag.ASIA, states[0].Session);
        Assert.Equal(SessionTag.FRANKFURT, states[1].Session);
        Assert.Equal(SessionTag.LONDON, last.Session);
        Assert.True(last.CurrentRange(SessionTag.ASIA)!.IsComplete);
        Assert.True(last.CurrentRange(SessionTag.FRANKFURT)!.IsComplete);
        Assert.False(last.CurrentRange(SessionTag.LONDON)!.IsComplete);
    }

    [Fact]
    public void Previous_range_rotates_on_next_day()
    {
        var engine = new SessionEngine();
        // Два дня: LONDON 01.04 и LONDON 02.04.
        var states = Feed(engine, T.Utc(2026, 4, 1, 7, 0), T.Utc(2026, 4, 2, 7, 10));
        var last = states.Last();

        var current = last.CurrentRange(SessionTag.LONDON)!;
        var previous = last.PreviousRange(SessionTag.LONDON)!;
        Assert.Equal(T.Date(2026, 4, 2), current.Window.AnchorLocalDate);
        Assert.Equal(T.Date(2026, 4, 1), previous.Window.AnchorLocalDate);
        Assert.Equal(54, previous.BarCount); // 4.5 часа × 12
        Assert.True(previous.IsComplete);
        Assert.Equal(2, current.BarCount);
        Assert.False(current.IsComplete);
        Assert.Null(last.PreviousRange(SessionTag.ASIA)); // ASIA 02.04 — первая ASIA в ленте
    }

    [Fact]
    public void Gold_profile_tags_asia_dead_but_still_tracks_asia_range()
    {
        var engine = new SessionEngine(profile: SessionProfile.ForSymbol("XAUUSD"));
        var state = engine.OnBar(T.Utc(2026, 4, 1, 0, 0), 2300.5, 2299.0);

        Assert.Equal(SessionTag.DEAD, state.Session);
        Assert.Equal(SessionTag.ASIA, state.WindowTag);
        Assert.Equal(SessionRole.Off, state.Role);
        Assert.False(state.IsSessionOpen);
        Assert.Equal(2300.5, state.CurrentRange(SessionTag.ASIA)!.High);
        Assert.Equal(2299.0, state.CurrentRange(SessionTag.ASIA)!.Low);

        var ny = engine.OnBar(T.Utc(2026, 4, 1, 13, 30), 2301.0, 2300.0);
        Assert.Equal(SessionTag.NY_CASH, ny.Session);
        Assert.Equal(SessionRole.Primary, ny.Role);
    }

    [Fact]
    public void Default_profile_marks_london_primary_and_others_secondary()
    {
        Assert.Equal(SessionRole.Primary, SessionProfile.Default.RoleOf(SessionTag.LONDON));
        Assert.Equal(SessionRole.Secondary, SessionProfile.Default.RoleOf(SessionTag.ASIA));
        Assert.Equal(SessionRole.Off, SessionProfile.Default.RoleOf(SessionTag.DEAD));
        Assert.Same(SessionProfile.Default, SessionProfile.ForSymbol("GER40"));
        Assert.Same(SessionProfile.Default, SessionProfile.ForSymbol("EURUSD"));
        Assert.Same(SessionProfile.Gold, SessionProfile.ForSymbol("xauusd"));
    }

    [Fact]
    public void Holiday_forces_dead()
    {
        var engine = new SessionEngine(holidays: new AlwaysHoliday());
        var state = engine.OnBar(T.Utc(2026, 4, 1, 8, 0), 1.1, 1.0);
        Assert.Equal(SessionTag.DEAD, state.Session);
        Assert.Equal(SessionTag.LONDON, state.WindowTag);
        Assert.True(state.IsHoliday);
        Assert.False(state.IsSessionOpen);
    }

    [Fact]
    public void Non_chronological_bars_are_rejected()
    {
        var engine = new SessionEngine();
        engine.OnBar(T.Utc(2026, 4, 1, 8, 0), 1.1, 1.0);
        Assert.Throws<InvalidOperationException>(() => engine.OnBar(T.Utc(2026, 4, 1, 8, 0), 1.1, 1.0));
        Assert.Throws<InvalidOperationException>(() => engine.OnBar(T.Utc(2026, 4, 1, 7, 55), 1.1, 1.0));
        Assert.Equal(1, engine.BarsProcessed);
    }

    [Fact]
    public void Invalid_bar_is_rejected()
    {
        var engine = new SessionEngine();
        Assert.Throws<ArgumentException>(() => engine.OnBar(T.Utc(2026, 4, 1, 8, 0), 1.0, 1.1));
        Assert.Throws<ArgumentException>(() => engine.OnBar(T.Utc(2026, 4, 1, 8, 5), double.NaN, 1.0));
    }

    [Fact]
    public void Dead_bars_do_not_create_ranges()
    {
        var engine = new SessionEngine();
        var state = engine.OnBar(T.Utc(2026, 4, 4, 12, 0), 1.1, 1.0); // суббота
        Assert.True(state.IsDead);
        Assert.Empty(state.Current);
        Assert.Empty(state.Previous);
    }

    [Fact]
    public void Full_week_feed_produces_seven_completed_ranges_per_session_day()
    {
        var engine = new SessionEngine();
        // Неделя 30.03 (Mon) 23:00 UTC предыдущего дня → 04.04 (Sat) 00:00 UTC, включая DST-разнобой марта.
        var states = Feed(engine, T.Utc(2026, 3, 29, 23, 0), T.Utc(2026, 4, 4, 0, 0));
        var last = states.Last();
        foreach (var tag in new[] { SessionTag.ASIA, SessionTag.FRANKFURT, SessionTag.LONDON, SessionTag.NY_PRE, SessionTag.NY_CASH, SessionTag.LONDON_CLOSE, SessionTag.NY_CLOSE })
        {
            var current = last.CurrentRange(tag)!;
            Assert.True(current.IsComplete, $"{tag} should be complete by Saturday");
            Assert.Equal(T.Date(2026, 4, 3), current.Window.AnchorLocalDate);
            Assert.Equal(T.Date(2026, 4, 2), last.PreviousRange(tag)!.Window.AnchorLocalDate);
            Assert.Equal((int)current.Window.Duration.TotalMinutes / 5, current.BarCount);
        }

        Assert.Equal(states.Count, engine.BarsProcessed);
    }
}
