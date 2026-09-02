using System;
using System.Collections.Generic;
using LionRegime.Core.Calendar;

namespace LionRegime.Core.Sessions;

/// <summary>
/// Слой 1 — Sessions. Стейтфул-движок: кормится ЗАКРЫТЫМИ барами в хронологическом порядке
/// (время открытия бара в UTC + High/Low) и отдаёт SessionState на каждый бар.
/// Ни одной строки торговой логики. Ни одной зависимости от cAlgo.
/// </summary>
public sealed class SessionEngine
{
    private readonly Dictionary<SessionTag, SessionRange> _current = new Dictionary<SessionTag, SessionRange>();
    private readonly Dictionary<SessionTag, SessionRange> _previous = new Dictionary<SessionTag, SessionRange>();
    private DateTime? _lastBarUtc;

    public SessionEngine(SessionSchedule? schedule = null, SessionProfile? profile = null, IHolidayCalendar? holidays = null)
    {
        Schedule = schedule ?? SessionSchedule.Default();
        Profile = profile ?? SessionProfile.Default;
        Holidays = holidays ?? NoHolidays.Instance;
    }

    public SessionSchedule Schedule { get; }

    public SessionProfile Profile { get; }

    public IHolidayCalendar Holidays { get; }

    public int BarsProcessed { get; private set; }

    /// <summary>
    /// Закрытый бар. openTimeUtc — время открытия бара (cAlgo: Bars.OpenTimes[i], UTC).
    /// Бары строго по возрастанию времени; повтор или откат назад — исключение (защита от lookahead и двойного учёта).
    /// </summary>
    public SessionState OnBar(DateTime openTimeUtc, double high, double low)
    {
        var utc = TimeZones.EnsureUtc(openTimeUtc);
        if (_lastBarUtc.HasValue && utc <= _lastBarUtc.Value)
        {
            throw new InvalidOperationException($"Bars must be strictly chronological: got {utc:O} after {_lastBarUtc.Value:O}");
        }

        _lastBarUtc = utc;

        var slot = Schedule.Classify(utc);
        CompleteExpired(utc);
        foreach (var window in slot.ActiveWindows)
        {
            RangeFor(window).AddBar(high, low);
        }

        var isHoliday = Holidays.IsHoliday(utc);
        var role = Profile.RoleOf(slot.Tag);
        var session = isHoliday || role == SessionRole.Off ? SessionTag.DEAD : slot.Tag;
        var isDead = session == SessionTag.DEAD;

        BarsProcessed++;
        return new SessionState(
            utc,
            TimeZones.ToIsrael(utc),
            session,
            slot.Tag,
            role,
            slot.MinutesIntoSession,
            !isDead && slot.IsSessionOpen,
            !isDead && slot.IsSessionClose,
            isHoliday,
            _current,
            _previous);
    }

    /// <summary>Классификация момента без состояния и без High/Low.</summary>
    public SessionSlot Classify(DateTime utc) => Schedule.Classify(utc);

    private SessionRange RangeFor(SessionWindow window)
    {
        if (_current.TryGetValue(window.Tag, out var current))
        {
            if (string.Equals(current.Window.Key, window.Key, StringComparison.Ordinal))
            {
                return current;
            }

            current.Complete();
            _previous[window.Tag] = current;
        }

        var fresh = new SessionRange(window);
        _current[window.Tag] = fresh;
        return fresh;
    }

    private void CompleteExpired(DateTime utc)
    {
        foreach (var range in _current.Values)
        {
            if (!range.IsComplete && range.Window.EndUtc <= utc)
            {
                range.Complete();
            }
        }
    }
}
