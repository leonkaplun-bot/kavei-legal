using LionRegime.Core.Sessions;
using Xunit;

namespace LionRegime.Core.Tests.Sessions;

public class SessionScheduleTests
{
    private readonly SessionSchedule _s = SessionSchedule.Default();

    [Theory]
    [InlineData(2026, 4, 1, 6, 30, SessionTag.FRANKFURT)]    // ASIA ∩ FRANKFURT → FRANKFURT
    [InlineData(2026, 4, 1, 5, 55, SessionTag.ASIA)]         // до Франкфурта
    [InlineData(2026, 4, 1, 15, 30, SessionTag.LONDON_CLOSE)] // NY_CASH ∩ LONDON_CLOSE → LONDON_CLOSE
    [InlineData(2026, 4, 1, 14, 55, SessionTag.NY_CASH)]
    [InlineData(2026, 3, 11, 12, 0, SessionTag.NY_PRE)]       // период B: LONDON ∩ NY_PRE → NY_PRE
    [InlineData(2026, 3, 11, 11, 25, SessionTag.LONDON)]
    [InlineData(2026, 4, 1, 16, 30, SessionTag.DEAD)]
    [InlineData(2026, 4, 1, 20, 30, SessionTag.DEAD)]
    [InlineData(2026, 4, 1, 22, 0, SessionTag.DEAD)]
    [InlineData(2026, 4, 1, 23, 0, SessionTag.ASIA)]          // ASIA следующего дня (Tokyo 02.04 08:00)
    public void Overlap_priority_and_gaps(int y, int mo, int d, int h, int mi, SessionTag expected)
    {
        Assert.Equal(expected, _s.Classify(T.Utc(y, mo, d, h, mi)).Tag);
    }

    [Fact]
    public void Overlapping_windows_are_all_reported_in_priority_order()
    {
        var slot = _s.Classify(T.Utc(2026, 4, 1, 6, 30));
        Assert.Equal(new[] { SessionTag.ASIA, SessionTag.FRANKFURT }, slot.ActiveWindows.Select(w => w.Tag).ToArray());
        Assert.Equal(SessionTag.FRANKFURT, slot.Window!.Tag);
    }

    [Theory]
    [InlineData(7, 0, true, false, 0)]
    [InlineData(7, 5, true, false, 5)]
    [InlineData(7, 10, true, false, 10)]
    [InlineData(7, 15, false, false, 15)]
    [InlineData(7, 35, false, false, 35)]
    [InlineData(11, 10, false, false, 250)]
    [InlineData(11, 15, false, true, 255)]
    [InlineData(11, 20, false, true, 260)]
    [InlineData(11, 25, false, true, 265)]
    public void London_open_close_flags_and_minutes(int h, int mi, bool isOpen, bool isClose, int minutesInto)
    {
        var slot = _s.Classify(T.Utc(2026, 4, 1, h, mi));
        Assert.Equal(SessionTag.LONDON, slot.Tag);
        Assert.Equal(isOpen, slot.IsSessionOpen);
        Assert.Equal(isClose, slot.IsSessionClose);
        Assert.Equal(minutesInto, slot.MinutesIntoSession);
    }

    [Fact]
    public void Dead_minutes_count_from_last_window_end()
    {
        // 01.04 лето: NY_CASH и LONDON_CLOSE оба заканчиваются 16:00 UTC.
        Assert.Equal(30, _s.Classify(T.Utc(2026, 4, 1, 16, 30)).MinutesIntoSession);
        // NY_CLOSE заканчивается 20:00 UTC.
        Assert.Equal(30, _s.Classify(T.Utc(2026, 4, 1, 20, 30)).MinutesIntoSession);
        // Воскресенье 12:00 UTC: последнее окно — NY_CLOSE пятницы 03.04, конец 20:00 UTC → 40 часов.
        Assert.Equal(40 * 60, _s.Classify(T.Utc(2026, 4, 5, 12, 0)).MinutesIntoSession);
    }

    [Fact]
    public void Weekend_is_dead_and_week_starts_with_monday_asia()
    {
        for (var t = T.Utc(2026, 4, 4, 0, 0); t < T.Utc(2026, 4, 5, 23, 0); t = t.AddMinutes(5))
        {
            Assert.True(_s.Classify(t).IsDead, $"{t:O} should be DEAD");
        }

        var mondayAsia = _s.Classify(T.Utc(2026, 4, 5, 23, 0));
        Assert.Equal(SessionTag.ASIA, mondayAsia.Tag);
        Assert.Equal(T.Date(2026, 4, 6), mondayAsia.Window!.AnchorLocalDate);
    }

    [Fact]
    public void Friday_ends_with_ny_close_and_no_saturday_windows()
    {
        Assert.Equal(SessionTag.NY_CLOSE, _s.Classify(T.Utc(2026, 4, 3, 19, 55)).Tag);
        Assert.True(_s.Classify(T.Utc(2026, 4, 3, 20, 0)).IsDead);
        Assert.Empty(_s.WindowsOnUtcDay(T.Utc(2026, 4, 4, 0, 0)));
    }

    [Fact]
    public void Windows_on_utc_day_are_sorted_and_unique()
    {
        var windows = _s.WindowsOnUtcDay(T.Utc(2026, 4, 1, 0, 0));
        Assert.Equal(windows.Select(w => w.Key).Distinct().Count(), windows.Count);
        for (var i = 1; i < windows.Count; i++)
        {
            Assert.True(windows[i - 1].StartUtc <= windows[i].StartUtc);
        }

        // 01.04 (среда): хвост ASIA 31.03→01.04, все 7 сессий дня, голова ASIA 01.04→02.04.
        Assert.Equal(8, windows.Count);
        Assert.Equal(SessionTag.ASIA, windows[0].Tag);
        Assert.Equal(SessionTag.ASIA, windows[7].Tag);
        Assert.Equal(T.Date(2026, 4, 2), windows[7].AnchorLocalDate);
    }

    [Fact]
    public void Unspecified_kind_is_accepted_as_utc()
    {
        var unspecified = new DateTime(2026, 4, 1, 7, 0, 0, DateTimeKind.Unspecified);
        Assert.Equal(SessionTag.LONDON, _s.Classify(unspecified).Tag);
    }

    [Fact]
    public void Schedule_rejects_duplicates_and_bad_windows()
    {
        var london = new SessionDefinition(SessionTag.LONDON, TimeZones.London, TimeSpan.FromHours(8), TimeSpan.FromHours(12.5));
        Assert.Throws<ArgumentException>(() => new SessionSchedule(new[] { london, london }));
        Assert.Throws<ArgumentException>(() => new SessionSchedule(Array.Empty<SessionDefinition>()));
        Assert.Throws<ArgumentException>(() => new SessionDefinition(SessionTag.DEAD, TimeZones.London, TimeSpan.Zero, TimeSpan.FromHours(1)));
        Assert.Throws<ArgumentOutOfRangeException>(() => new SessionDefinition(SessionTag.LONDON, TimeZones.London, TimeSpan.FromHours(9), TimeSpan.FromHours(8)));
        Assert.Throws<ArgumentOutOfRangeException>(() => new SessionDefinition(SessionTag.LONDON, TimeZones.London, TimeSpan.FromHours(23), TimeSpan.FromHours(25)));
    }

    [Fact]
    public void Default_open_close_window_is_three_m5_bars()
    {
        Assert.Equal(15, _s.OpenWindowMinutes);
        Assert.Equal(15, _s.CloseWindowMinutes);
    }
}
