using System;
using System.Globalization;

namespace LionRegime.Core.Sessions;

/// <summary>Одно конкретное окно сессии в UTC, например LONDON за 2026-04-01.</summary>
public sealed class SessionWindow
{
    public SessionWindow(SessionTag tag, DateTime anchorLocalDate, DateTime startUtc, DateTime endUtc)
    {
        if (endUtc <= startUtc)
        {
            throw new ArgumentException($"{tag}: EndUtc must be after StartUtc", nameof(endUtc));
        }

        Tag = tag;
        AnchorLocalDate = anchorLocalDate.Date;
        StartUtc = TimeZones.EnsureUtc(startUtc);
        EndUtc = TimeZones.EnsureUtc(endUtc);
    }

    public SessionTag Tag { get; }

    /// <summary>Дата в таймзоне якоря (только дата). Это ключ «торгового дня» сессии.</summary>
    public DateTime AnchorLocalDate { get; }

    public DateTime StartUtc { get; }

    /// <summary>Исключительная граница: бар с OpenTime == EndUtc уже не в сессии.</summary>
    public DateTime EndUtc { get; }

    public TimeSpan Duration => EndUtc - StartUtc;

    public string Key => Tag + "@" + AnchorLocalDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);

    public bool Contains(DateTime utc)
    {
        var t = TimeZones.EnsureUtc(utc);
        return t >= StartUtc && t < EndUtc;
    }

    public override string ToString() =>
        string.Format(CultureInfo.InvariantCulture, "{0} {1:yyyy-MM-dd HH:mm}Z-{2:HH:mm}Z", Key, StartUtc, EndUtc);
}
