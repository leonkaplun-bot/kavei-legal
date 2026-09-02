using LionRegime.Core.Sessions;
using Xunit;

namespace LionRegime.Core.Tests.Sessions;

/// <summary>
/// Проверяем, что системная tz-база знает правила 2026 года для четырёх зон.
/// Если эти тесты падают — проблема в окружении (tzdata), а не в SessionEngine.
/// </summary>
public class TimeZoneFactsTests
{
    [Fact]
    public void All_zones_resolve_on_this_platform()
    {
        Assert.NotNull(TimeZones.Israel);
        Assert.NotNull(TimeZones.London);
        Assert.NotNull(TimeZones.Berlin);
        Assert.NotNull(TimeZones.NewYork);
        Assert.NotNull(TimeZones.Tokyo);
        Assert.Equal(TimeSpan.FromHours(9), TimeZones.OffsetAt(T.Utc(2026, 1, 1, 0, 0), TimeZones.Tokyo));
        Assert.Equal(TimeSpan.FromHours(9), TimeZones.OffsetAt(T.Utc(2026, 7, 1, 0, 0), TimeZones.Tokyo));
    }

    // Israel: DST с пятницы 2026-03-27 02:00 (= 00:00 UTC) по воскресенье 2026-10-25 02:00 (= 23:00 UTC 24.10).
    [Theory]
    [InlineData(2026, 3, 26, 23, 59, 2)]
    [InlineData(2026, 3, 27, 0, 0, 3)]
    [InlineData(2026, 7, 1, 12, 0, 3)]
    [InlineData(2026, 10, 24, 22, 59, 3)]
    [InlineData(2026, 10, 24, 23, 0, 2)]
    [InlineData(2026, 12, 1, 12, 0, 2)]
    public void Israel_offset_2026(int y, int mo, int d, int h, int mi, int expectedHours)
    {
        Assert.Equal(TimeSpan.FromHours(expectedHours), TimeZones.OffsetAt(T.Utc(y, mo, d, h, mi), TimeZones.Israel));
    }

    // London/Berlin: DST с воскресенья 2026-03-29 01:00 UTC по воскресенье 2026-10-25 01:00 UTC.
    [Theory]
    [InlineData(2026, 3, 29, 0, 59, 0, 1)]
    [InlineData(2026, 3, 29, 1, 0, 1, 2)]
    [InlineData(2026, 10, 25, 0, 59, 1, 2)]
    [InlineData(2026, 10, 25, 1, 0, 0, 1)]
    public void London_and_Berlin_offset_2026(int y, int mo, int d, int h, int mi, int londonHours, int berlinHours)
    {
        var t = T.Utc(y, mo, d, h, mi);
        Assert.Equal(TimeSpan.FromHours(londonHours), TimeZones.OffsetAt(t, TimeZones.London));
        Assert.Equal(TimeSpan.FromHours(berlinHours), TimeZones.OffsetAt(t, TimeZones.Berlin));
    }

    // New York: DST с воскресенья 2026-03-08 07:00 UTC по воскресенье 2026-11-01 06:00 UTC.
    [Theory]
    [InlineData(2026, 3, 8, 6, 59, -5)]
    [InlineData(2026, 3, 8, 7, 0, -4)]
    [InlineData(2026, 11, 1, 5, 59, -4)]
    [InlineData(2026, 11, 1, 6, 0, -5)]
    public void NewYork_offset_2026(int y, int mo, int d, int h, int mi, int expectedHours)
    {
        Assert.Equal(TimeSpan.FromHours(expectedHours), TimeZones.OffsetAt(T.Utc(y, mo, d, h, mi), TimeZones.NewYork));
    }

    [Theory]
    [InlineData(2026, 3, 26, 23, 59, "2026-03-27 01:59")]
    [InlineData(2026, 3, 27, 0, 0, "2026-03-27 03:00")]
    [InlineData(2026, 10, 24, 22, 59, "2026-10-25 01:59")]
    [InlineData(2026, 10, 24, 23, 0, "2026-10-25 01:00")]
    public void ToIsrael_display_across_transitions(int y, int mo, int d, int h, int mi, string expectedIl)
    {
        Assert.Equal(expectedIl, T.Il(T.Utc(y, mo, d, h, mi)));
    }

    [Fact]
    public void EnsureUtc_treats_unspecified_as_utc()
    {
        var unspecified = new DateTime(2026, 4, 1, 7, 0, 0, DateTimeKind.Unspecified);
        var utc = TimeZones.EnsureUtc(unspecified);
        Assert.Equal(DateTimeKind.Utc, utc.Kind);
        Assert.Equal(unspecified.Ticks, utc.Ticks);
    }

    [Fact]
    public void LocalToUtc_shifts_forward_out_of_dst_gap()
    {
        // 2026-03-29 01:30 не существует в Лондоне (01:00 → 02:00). Ожидаем 02:00 BST = 01:00 UTC.
        var gap = new DateTime(2026, 3, 29, 1, 30, 0, DateTimeKind.Unspecified);
        Assert.True(TimeZones.London.IsInvalidTime(gap));
        Assert.Equal(T.Utc(2026, 3, 29, 1, 0), TimeZones.LocalToUtc(gap, TimeZones.London));
    }

    [Fact]
    public void Find_falls_back_to_next_id()
    {
        var zone = TimeZones.Find("Not/AZone", "Europe/London", "GMT Standard Time");
        Assert.Equal(TimeZones.London.Id, zone.Id);
        Assert.Throws<TimeZoneNotFoundException>(() => TimeZones.Find("Not/AZone", "Also/Missing"));
    }
}
