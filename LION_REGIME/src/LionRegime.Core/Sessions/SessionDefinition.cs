using System;
using System.Globalization;

namespace LionRegime.Core.Sessions;

/// <summary>
/// Определение сессии: тег + таймзона якоря + wall-clock границы в этой зоне.
/// Сессия привязана к своему домашнему рынку (LONDON → Europe/London, NY_* → America/New_York и т.д.),
/// поэтому DST каждого рынка обрабатывается его tz-правилами, а не хардкод-смещениями.
/// Сессии через полночь не поддерживаются (LocalEnd ≤ 24:00).
/// </summary>
public sealed class SessionDefinition
{
    public SessionDefinition(SessionTag tag, TimeZoneInfo anchorZone, TimeSpan localStart, TimeSpan localEnd)
    {
        if (tag == SessionTag.DEAD)
        {
            throw new ArgumentException("DEAD is not a session, it is the absence of one", nameof(tag));
        }

        if (localStart < TimeSpan.Zero || localStart >= TimeSpan.FromHours(24))
        {
            throw new ArgumentOutOfRangeException(nameof(localStart), $"{tag}: LocalStart must be within [00:00, 24:00)");
        }

        if (localEnd <= localStart || localEnd > TimeSpan.FromHours(24))
        {
            throw new ArgumentOutOfRangeException(nameof(localEnd), $"{tag}: LocalEnd must be > LocalStart and <= 24:00");
        }

        Tag = tag;
        AnchorZone = anchorZone ?? throw new ArgumentNullException(nameof(anchorZone));
        LocalStart = localStart;
        LocalEnd = localEnd;
    }

    public SessionTag Tag { get; }

    public TimeZoneInfo AnchorZone { get; }

    public TimeSpan LocalStart { get; }

    /// <summary>Исключительная граница.</summary>
    public TimeSpan LocalEnd { get; }

    public TimeSpan LocalDuration => LocalEnd - LocalStart;

    /// <summary>
    /// Окно сессии для даты в зоне якоря. null — выходной (Sat/Sun по локальной дате якоря).
    /// ASIA за понедельник (Tokyo Mon 08:00) стартует в воскресенье 23:00 UTC — это корректно.
    /// </summary>
    public SessionWindow? WindowFor(DateTime anchorLocalDate)
    {
        var date = anchorLocalDate.Date;
        if (date.DayOfWeek == DayOfWeek.Saturday || date.DayOfWeek == DayOfWeek.Sunday)
        {
            return null;
        }

        var startUtc = TimeZones.LocalToUtc(date + LocalStart, AnchorZone);
        var endUtc = TimeZones.LocalToUtc(date + LocalEnd, AnchorZone);
        return new SessionWindow(Tag, date, startUtc, endUtc);
    }

    public override string ToString() =>
        string.Format(CultureInfo.InvariantCulture, "{0} {1:hh\\:mm}-{2:hh\\:mm} {3}", Tag, LocalStart, LocalEnd, AnchorZone.Id);
}
