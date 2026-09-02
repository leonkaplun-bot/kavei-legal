using System;
using System.Collections.Generic;
using System.Linq;

namespace LionRegime.Core.Sessions;

/// <summary>
/// Расписание сессий: набор SessionDefinition + ширина open/close-окон.
/// Без торгового состояния; кэширует окна по UTC-дате. Классификация — по времени ОТКРЫТИЯ бара.
/// </summary>
public sealed class SessionSchedule
{
    /// <summary>15 минут = 3 бара M5. Дефолт выбран в сессии 1, в ТЗ значение не задано.</summary>
    public const int DefaultOpenWindowMinutes = 15;

    /// <summary>15 минут = 3 бара M5. Дефолт выбран в сессии 1, в ТЗ значение не задано.</summary>
    public const int DefaultCloseWindowMinutes = 15;

    private const int DeadLookbackDays = 7;

    private readonly Dictionary<DateTime, List<SessionWindow>> _cache = new Dictionary<DateTime, List<SessionWindow>>();

    public SessionSchedule(
        IEnumerable<SessionDefinition> definitions,
        int openWindowMinutes = DefaultOpenWindowMinutes,
        int closeWindowMinutes = DefaultCloseWindowMinutes)
    {
        if (definitions is null)
        {
            throw new ArgumentNullException(nameof(definitions));
        }

        if (openWindowMinutes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(openWindowMinutes));
        }

        if (closeWindowMinutes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(closeWindowMinutes));
        }

        var defs = definitions.OrderBy(d => (int)d.Tag).ToList();
        if (defs.Count == 0)
        {
            throw new ArgumentException("At least one session definition is required", nameof(definitions));
        }

        var duplicate = defs.GroupBy(d => d.Tag).FirstOrDefault(g => g.Count() > 1);
        if (duplicate != null)
        {
            throw new ArgumentException($"Duplicate session definition for {duplicate.Key}", nameof(definitions));
        }

        Definitions = defs;
        OpenWindowMinutes = openWindowMinutes;
        CloseWindowMinutes = closeWindowMinutes;
    }

    /// <summary>Определения, отсортированные по приоритету (возрастание SessionTag).</summary>
    public IReadOnlyList<SessionDefinition> Definitions { get; }

    public int OpenWindowMinutes { get; }

    public int CloseWindowMinutes { get; }

    /// <summary>Дефолтные сессии из ТЗ.</summary>
    public static SessionSchedule Default() => new SessionSchedule(DefaultDefinitions());

    /// <summary>
    /// Таблица из ТЗ дана в Israel-summer (UTC+3). Каждая сессия привязана к домашнему рынку так,
    /// чтобы летом совпадать с таблицей; зимой границы двигаются вместе со своим рынком, а не с Израилем.
    /// </summary>
    public static IReadOnlyList<SessionDefinition> DefaultDefinitions() => new[]
    {
        // ASIA 02:00–10:00 IL = 23:00–07:00 UTC = Tokyo 08:00–16:00. Токио без DST → фиксировано в UTC круглый год.
        new SessionDefinition(SessionTag.ASIA, TimeZones.Tokyo, At(8, 0), At(16, 0)),

        // FRANKFURT 09:00–10:00 IL = 06:00–07:00 UTC = Berlin 08:00–09:00 (Xetra pre-open).
        new SessionDefinition(SessionTag.FRANKFURT, TimeZones.Berlin, At(8, 0), At(9, 0)),

        // LONDON 10:00–14:30 IL = 07:00–11:30 UTC = London 08:00–12:30.
        new SessionDefinition(SessionTag.LONDON, TimeZones.London, At(8, 0), At(12, 30)),

        // NY_PRE 14:30–16:30 IL = 11:30–13:30 UTC = New York 07:30–09:30 (новости 08:30 ET).
        new SessionDefinition(SessionTag.NY_PRE, TimeZones.NewYork, At(7, 30), At(9, 30)),

        // NY_CASH 16:30–19:00 IL = 13:30–16:00 UTC = New York 09:30–12:00 (NYSE open).
        new SessionDefinition(SessionTag.NY_CASH, TimeZones.NewYork, At(9, 30), At(12, 0)),

        // LONDON_CLOSE 18:00–19:00 IL = 15:00–16:00 UTC = London 16:00–17:00 (London fix 16:00).
        new SessionDefinition(SessionTag.LONDON_CLOSE, TimeZones.London, At(16, 0), At(17, 0)),

        // NY_CLOSE 22:00–23:00 IL = 19:00–20:00 UTC = New York 15:00–16:00 (NYSE close).
        new SessionDefinition(SessionTag.NY_CLOSE, TimeZones.NewYork, At(15, 0), At(16, 0)),
    };

    /// <summary>Все окна, пересекающие данные UTC-сутки, по возрастанию StartUtc. Кэшируется.</summary>
    public IReadOnlyList<SessionWindow> WindowsOnUtcDay(DateTime utcDate)
    {
        var dayStart = TimeZones.EnsureUtc(utcDate).Date;
        if (_cache.TryGetValue(dayStart, out var cached))
        {
            return cached;
        }

        var dayEnd = dayStart.AddDays(1);
        var list = new List<SessionWindow>();
        var seen = new HashSet<string>(StringComparer.Ordinal);

        foreach (var def in Definitions)
        {
            // Локальная дата якоря в момент начала UTC-суток; окна соседних локальных дат могут пересекать эти сутки.
            var localDate = TimeZones.ToZone(dayStart, def.AnchorZone).Date;
            for (var k = -1; k <= 1; k++)
            {
                var window = def.WindowFor(localDate.AddDays(k));
                if (window is null || window.EndUtc <= dayStart || window.StartUtc >= dayEnd)
                {
                    continue;
                }

                if (seen.Add(window.Key))
                {
                    list.Add(window);
                }
            }
        }

        list.Sort((a, b) =>
        {
            var byStart = a.StartUtc.CompareTo(b.StartUtc);
            return byStart != 0 ? byStart : ((int)a.Tag).CompareTo((int)b.Tag);
        });

        _cache[dayStart] = list;
        return list;
    }

    /// <summary>Окна, содержащие момент, по возрастанию приоритета (последнее — победитель).</summary>
    public IReadOnlyList<SessionWindow> WindowsContaining(DateTime utc)
    {
        var t = TimeZones.EnsureUtc(utc);
        var result = new List<SessionWindow>();
        foreach (var window in WindowsOnUtcDay(t.Date))
        {
            if (window.Contains(t))
            {
                result.Add(window);
            }
        }

        result.Sort((a, b) => ((int)a.Tag).CompareTo((int)b.Tag));
        return result;
    }

    public SessionSlot Classify(DateTime utc)
    {
        var t = TimeZones.EnsureUtc(utc);
        var active = WindowsContaining(t);
        if (active.Count == 0)
        {
            return new SessionSlot(t, SessionTag.DEAD, null, MinutesSinceLastWindowEnd(t), false, false, active);
        }

        var window = active[active.Count - 1];
        var into = (int)Math.Floor((t - window.StartUtc).TotalMinutes);
        var remaining = (int)Math.Ceiling((window.EndUtc - t).TotalMinutes);
        var isOpen = into < OpenWindowMinutes;
        var isClose = remaining <= CloseWindowMinutes;
        return new SessionSlot(t, window.Tag, window, into, isOpen, isClose, active);
    }

    private static TimeSpan At(int hours, int minutes) => new TimeSpan(hours, minutes, 0);

    private int MinutesSinceLastWindowEnd(DateTime utc)
    {
        for (var back = 0; back <= DeadLookbackDays; back++)
        {
            DateTime? lastEnd = null;
            foreach (var window in WindowsOnUtcDay(utc.Date.AddDays(-back)))
            {
                if (window.EndUtc <= utc && (!lastEnd.HasValue || window.EndUtc > lastEnd.Value))
                {
                    lastEnd = window.EndUtc;
                }
            }

            if (lastEnd.HasValue)
            {
                return (int)Math.Floor((utc - lastEnd.Value).TotalMinutes);
            }
        }

        return -1;
    }
}
