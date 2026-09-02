using LionRegime.Core.Sessions;
using Xunit;

namespace LionRegime.Core.Tests.Sessions;

/// <summary>
/// DST-переходы 2026: 08.03 (US), 27.03 (Israel), 29.03 (EU), 25.10 (Israel + EU), 01.11 (US).
/// Пять периодов с разным набором смещений — окна каждой сессии в UTC и их вид в Israel time.
/// </summary>
public class SessionScheduleDstTests
{
    private readonly SessionSchedule _s = SessionSchedule.Default();

    // Период A — полная зима (Wed 04.03): IL+2, LON+0, BER+1, NY-5.
    // Все сессии совпадают с таблицей ТЗ по израильским часам, кроме ASIA (Токио не двигается): 01:00–09:00.
    [Theory]
    [InlineData(SessionTag.ASIA, 2026, 3, 3, 23, 0, 2026, 3, 4, 7, 0, "2026-03-04 01:00", "2026-03-04 09:00")]
    [InlineData(SessionTag.FRANKFURT, 2026, 3, 4, 7, 0, 2026, 3, 4, 8, 0, "2026-03-04 09:00", "2026-03-04 10:00")]
    [InlineData(SessionTag.LONDON, 2026, 3, 4, 8, 0, 2026, 3, 4, 12, 30, "2026-03-04 10:00", "2026-03-04 14:30")]
    [InlineData(SessionTag.NY_PRE, 2026, 3, 4, 12, 30, 2026, 3, 4, 14, 30, "2026-03-04 14:30", "2026-03-04 16:30")]
    [InlineData(SessionTag.NY_CASH, 2026, 3, 4, 14, 30, 2026, 3, 4, 17, 0, "2026-03-04 16:30", "2026-03-04 19:00")]
    [InlineData(SessionTag.LONDON_CLOSE, 2026, 3, 4, 16, 0, 2026, 3, 4, 17, 0, "2026-03-04 18:00", "2026-03-04 19:00")]
    [InlineData(SessionTag.NY_CLOSE, 2026, 3, 4, 20, 0, 2026, 3, 4, 21, 0, "2026-03-04 22:00", "2026-03-04 23:00")]
    public void Period_A_full_winter(SessionTag tag, int sy, int sm, int sd, int sh, int smi, int ey, int em, int ed, int eh, int emi, string ilStart, string ilEnd)
    {
        AssertWindow(tag, T.Date(2026, 3, 4), T.Utc(sy, sm, sd, sh, smi), T.Utc(ey, em, ed, eh, emi), ilStart, ilEnd);
    }

    // Период B — только США на DST (Wed 11.03): IL+2, LON+0, BER+1, NY-4.
    // NY-сессии приезжают на час раньше по Израилю; NY_PRE пересекается с LONDON.
    [Theory]
    [InlineData(SessionTag.LONDON, 2026, 3, 11, 8, 0, 2026, 3, 11, 12, 30, "2026-03-11 10:00", "2026-03-11 14:30")]
    [InlineData(SessionTag.NY_PRE, 2026, 3, 11, 11, 30, 2026, 3, 11, 13, 30, "2026-03-11 13:30", "2026-03-11 15:30")]
    [InlineData(SessionTag.NY_CASH, 2026, 3, 11, 13, 30, 2026, 3, 11, 16, 0, "2026-03-11 15:30", "2026-03-11 18:00")]
    [InlineData(SessionTag.LONDON_CLOSE, 2026, 3, 11, 16, 0, 2026, 3, 11, 17, 0, "2026-03-11 18:00", "2026-03-11 19:00")]
    [InlineData(SessionTag.NY_CLOSE, 2026, 3, 11, 19, 0, 2026, 3, 11, 20, 0, "2026-03-11 21:00", "2026-03-11 22:00")]
    public void Period_B_us_dst_only(SessionTag tag, int sy, int sm, int sd, int sh, int smi, int ey, int em, int ed, int eh, int emi, string ilStart, string ilEnd)
    {
        AssertWindow(tag, T.Date(2026, 3, 11), T.Utc(sy, sm, sd, sh, smi), T.Utc(ey, em, ed, eh, emi), ilStart, ilEnd);
    }

    // Период C — Израиль уже на DST, Европа ещё нет (Fri 27.03): IL+3, LON+0, BER+1, NY-4.
    // Единственный торговый день с таким набором. LONDON по Израилю 11:00–15:30.
    // ASIA этой ночи пересекает израильский перевод часов (00:00 UTC): старт 01:00 IL, конец 10:00 IL.
    [Theory]
    [InlineData(SessionTag.ASIA, 2026, 3, 26, 23, 0, 2026, 3, 27, 7, 0, "2026-03-27 01:00", "2026-03-27 10:00")]
    [InlineData(SessionTag.FRANKFURT, 2026, 3, 27, 7, 0, 2026, 3, 27, 8, 0, "2026-03-27 10:00", "2026-03-27 11:00")]
    [InlineData(SessionTag.LONDON, 2026, 3, 27, 8, 0, 2026, 3, 27, 12, 30, "2026-03-27 11:00", "2026-03-27 15:30")]
    [InlineData(SessionTag.NY_CASH, 2026, 3, 27, 13, 30, 2026, 3, 27, 16, 0, "2026-03-27 16:30", "2026-03-27 19:00")]
    public void Period_C_israel_dst_europe_not_yet(SessionTag tag, int sy, int sm, int sd, int sh, int smi, int ey, int em, int ed, int eh, int emi, string ilStart, string ilEnd)
    {
        AssertWindow(tag, T.Date(2026, 3, 27), T.Utc(sy, sm, sd, sh, smi), T.Utc(ey, em, ed, eh, emi), ilStart, ilEnd);
    }

    // Период D — полное лето (Wed 01.04): IL+3, LON+1, BER+2, NY-4. Таблица ТЗ воспроизводится точно.
    [Theory]
    [InlineData(SessionTag.ASIA, 2026, 3, 31, 23, 0, 2026, 4, 1, 7, 0, "2026-04-01 02:00", "2026-04-01 10:00")]
    [InlineData(SessionTag.FRANKFURT, 2026, 4, 1, 6, 0, 2026, 4, 1, 7, 0, "2026-04-01 09:00", "2026-04-01 10:00")]
    [InlineData(SessionTag.LONDON, 2026, 4, 1, 7, 0, 2026, 4, 1, 11, 30, "2026-04-01 10:00", "2026-04-01 14:30")]
    [InlineData(SessionTag.NY_PRE, 2026, 4, 1, 11, 30, 2026, 4, 1, 13, 30, "2026-04-01 14:30", "2026-04-01 16:30")]
    [InlineData(SessionTag.NY_CASH, 2026, 4, 1, 13, 30, 2026, 4, 1, 16, 0, "2026-04-01 16:30", "2026-04-01 19:00")]
    [InlineData(SessionTag.LONDON_CLOSE, 2026, 4, 1, 15, 0, 2026, 4, 1, 16, 0, "2026-04-01 18:00", "2026-04-01 19:00")]
    [InlineData(SessionTag.NY_CLOSE, 2026, 4, 1, 19, 0, 2026, 4, 1, 20, 0, "2026-04-01 22:00", "2026-04-01 23:00")]
    public void Period_D_full_summer_matches_spec_table(SessionTag tag, int sy, int sm, int sd, int sh, int smi, int ey, int em, int ed, int eh, int emi, string ilStart, string ilEnd)
    {
        AssertWindow(tag, T.Date(2026, 4, 1), T.Utc(sy, sm, sd, sh, smi), T.Utc(ey, em, ed, eh, emi), ilStart, ilEnd);
    }

    // Период E — Израиль и Европа вернулись на зиму, США ещё на DST (Wed 28.10): IL+2, LON+0, BER+1, NY-4.
    [Theory]
    [InlineData(SessionTag.LONDON, 2026, 10, 28, 8, 0, 2026, 10, 28, 12, 30, "2026-10-28 10:00", "2026-10-28 14:30")]
    [InlineData(SessionTag.NY_PRE, 2026, 10, 28, 11, 30, 2026, 10, 28, 13, 30, "2026-10-28 13:30", "2026-10-28 15:30")]
    [InlineData(SessionTag.NY_CASH, 2026, 10, 28, 13, 30, 2026, 10, 28, 16, 0, "2026-10-28 15:30", "2026-10-28 18:00")]
    [InlineData(SessionTag.NY_CLOSE, 2026, 10, 28, 19, 0, 2026, 10, 28, 20, 0, "2026-10-28 21:00", "2026-10-28 22:00")]
    public void Period_E_europe_winter_us_still_dst(SessionTag tag, int sy, int sm, int sd, int sh, int smi, int ey, int em, int ed, int eh, int emi, string ilStart, string ilEnd)
    {
        AssertWindow(tag, T.Date(2026, 10, 28), T.Utc(sy, sm, sd, sh, smi), T.Utc(ey, em, ed, eh, emi), ilStart, ilEnd);
    }

    // Период F — полная зима после 01.11 (Wed 04.11): как период A.
    [Theory]
    [InlineData(SessionTag.LONDON, 2026, 11, 4, 8, 0, 2026, 11, 4, 12, 30, "2026-11-04 10:00", "2026-11-04 14:30")]
    [InlineData(SessionTag.NY_CASH, 2026, 11, 4, 14, 30, 2026, 11, 4, 17, 0, "2026-11-04 16:30", "2026-11-04 19:00")]
    [InlineData(SessionTag.NY_CLOSE, 2026, 11, 4, 20, 0, 2026, 11, 4, 21, 0, "2026-11-04 22:00", "2026-11-04 23:00")]
    public void Period_F_full_winter_again(SessionTag tag, int sy, int sm, int sd, int sh, int smi, int ey, int em, int ed, int eh, int emi, string ilStart, string ilEnd)
    {
        AssertWindow(tag, T.Date(2026, 11, 4), T.Utc(sy, sm, sd, sh, smi), T.Utc(ey, em, ed, eh, emi), ilStart, ilEnd);
    }

    [Fact]
    public void London_window_shifts_by_one_hour_in_utc_across_march_transition()
    {
        var friBefore = T.Window(_s, SessionTag.LONDON, T.Date(2026, 3, 27));
        var monAfter = T.Window(_s, SessionTag.LONDON, T.Date(2026, 3, 30));
        Assert.Equal(8, friBefore.StartUtc.Hour);
        Assert.Equal(7, monAfter.StartUtc.Hour);
        Assert.Equal(friBefore.Duration, monAfter.Duration);
    }

    [Fact]
    public void NewYork_window_shifts_by_one_hour_in_utc_across_november_transition()
    {
        var friBefore = T.Window(_s, SessionTag.NY_CASH, T.Date(2026, 10, 30));
        var monAfter = T.Window(_s, SessionTag.NY_CASH, T.Date(2026, 11, 2));
        Assert.Equal(T.Utc(2026, 10, 30, 13, 30), friBefore.StartUtc);
        Assert.Equal(T.Utc(2026, 11, 2, 14, 30), monAfter.StartUtc);
        Assert.Equal(friBefore.Duration, monAfter.Duration);
    }

    [Fact]
    public void Session_durations_never_change_across_the_year()
    {
        // Смысл привязки к домашней зоне: длительность сессии не зависит от DST.
        var expected = _s.Definitions.ToDictionary(d => d.Tag, d => d.LocalDuration);
        for (var day = T.Utc(2026, 1, 1, 0, 0); day < T.Utc(2027, 1, 1, 0, 0); day = day.AddDays(1))
        {
            foreach (var w in _s.WindowsOnUtcDay(day))
            {
                Assert.Equal(expected[w.Tag], w.Duration);
            }
        }
    }

    [Fact]
    public void Every_weekday_of_2026_has_exactly_one_window_per_session()
    {
        var keys = new HashSet<string>(StringComparer.Ordinal);
        for (var day = T.Utc(2025, 12, 31, 0, 0); day <= T.Utc(2027, 1, 1, 0, 0); day = day.AddDays(1))
        {
            foreach (var w in _s.WindowsOnUtcDay(day))
            {
                if (w.AnchorLocalDate.Year == 2026)
                {
                    keys.Add(w.Key);
                }
            }
        }

        var weekdays = Enumerable.Range(0, 365)
            .Select(i => new DateTime(2026, 1, 1).AddDays(i))
            .Count(d => d.DayOfWeek != DayOfWeek.Saturday && d.DayOfWeek != DayOfWeek.Sunday);

        foreach (var def in _s.Definitions)
        {
            var count = keys.Count(k => k.StartsWith(def.Tag + "@", StringComparison.Ordinal));
            Assert.True(count == weekdays, $"{def.Tag}: expected {weekdays} windows in 2026, found {count}");
        }
    }

    [Fact]
    public void Classify_never_throws_for_any_m5_bar_of_2026()
    {
        var bars = 0;
        var dead = 0;
        for (var t = T.Utc(2026, 1, 1, 0, 0); t < T.Utc(2027, 1, 1, 0, 0); t = t.AddMinutes(5))
        {
            var slot = _s.Classify(t);
            bars++;
            if (slot.IsDead)
            {
                dead++;
            }
            else
            {
                Assert.NotNull(slot.Window);
                Assert.InRange(slot.MinutesIntoSession, 0, (int)slot.Window!.Duration.TotalMinutes - 1);
            }
        }

        Assert.Equal(365 * 24 * 12, bars);
        // Sat + Sun + ночные дыры: DEAD обязан быть заметной долей, но не всем.
        Assert.InRange((double)dead / bars, 0.35, 0.75);
    }

    private void AssertWindow(SessionTag tag, DateTime anchorLocalDate, DateTime startUtc, DateTime endUtc, string ilStart, string ilEnd)
    {
        var w = T.Window(_s, tag, anchorLocalDate);
        Assert.Equal(startUtc, w.StartUtc);
        Assert.Equal(endUtc, w.EndUtc);
        Assert.Equal(ilStart, T.Il(w.StartUtc));
        Assert.Equal(ilEnd, T.Il(w.EndUtc));

        // Классификация по границам: первый бар внутри, бар на EndUtc — уже нет.
        Assert.Equal(tag, _s.WindowsContaining(startUtc).Select(x => x.Tag).Max());
        Assert.DoesNotContain(tag, _s.WindowsContaining(endUtc).Select(x => x.Tag));
    }
}
