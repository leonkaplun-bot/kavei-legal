using System;

namespace LionRegime.Core.Sessions;

/// <summary>
/// Единая точка доступа к таймзонам. Все расчёты — в UTC; Israel — только для отображения.
/// Идентификаторы ищутся сначала по IANA (Linux/macOS, Windows с ICU), затем по Windows-id.
/// Никаких хардкод-смещений: DST решает TimeZoneInfo и системная tz-база.
/// </summary>
public static class TimeZones
{
    public static readonly TimeZoneInfo Israel = Find("Asia/Jerusalem", "Israel Standard Time");
    public static readonly TimeZoneInfo London = Find("Europe/London", "GMT Standard Time");
    public static readonly TimeZoneInfo Berlin = Find("Europe/Berlin", "W. Europe Standard Time");
    public static readonly TimeZoneInfo NewYork = Find("America/New_York", "Eastern Standard Time");
    public static readonly TimeZoneInfo Tokyo = Find("Asia/Tokyo", "Tokyo Standard Time");

    public static TimeZoneInfo Utc => TimeZoneInfo.Utc;

    /// <summary>Первый найденный идентификатор из списка. Бросает, если не найден ни один.</summary>
    public static TimeZoneInfo Find(params string[] ids)
    {
        foreach (var id in ids)
        {
            try
            {
                return TimeZoneInfo.FindSystemTimeZoneById(id);
            }
            catch (TimeZoneNotFoundException)
            {
                // пробуем следующий id
            }
            catch (InvalidTimeZoneException)
            {
                // пробуем следующий id
            }
        }

        throw new TimeZoneNotFoundException("None of the time zone ids were found: " + string.Join(", ", ids));
    }

    /// <summary>
    /// Приводит DateTime к Kind=Utc. Unspecified трактуется как UTC —
    /// cAlgo API отдаёт Bars.OpenTimes и Server.Time в UTC.
    /// </summary>
    public static DateTime EnsureUtc(DateTime t)
    {
        switch (t.Kind)
        {
            case DateTimeKind.Utc:
                return t;
            case DateTimeKind.Local:
                return t.ToUniversalTime();
            default:
                return DateTime.SpecifyKind(t, DateTimeKind.Utc);
        }
    }

    public static DateTime ToIsrael(DateTime utc) => ToZone(utc, Israel);

    public static DateTime ToZone(DateTime utc, TimeZoneInfo zone) =>
        TimeZoneInfo.ConvertTimeFromUtc(EnsureUtc(utc), zone);

    public static TimeSpan OffsetAt(DateTime utc, TimeZoneInfo zone) => zone.GetUtcOffset(EnsureUtc(utc));

    /// <summary>
    /// Wall-clock время зоны → UTC.
    /// Время в DST-дыре (не существует, например 01:30 в ночь весеннего перевода) сдвигается вперёд
    /// до первого существующего. Неоднозначное время (осенний повтор часа) берётся по стандартному
    /// смещению — это документированное поведение TimeZoneInfo.ConvertTimeToUtc.
    /// </summary>
    public static DateTime LocalToUtc(DateTime local, TimeZoneInfo zone)
    {
        var t = DateTime.SpecifyKind(local, DateTimeKind.Unspecified);
        var guard = 0;
        while (zone.IsInvalidTime(t))
        {
            t = t.AddMinutes(15);
            if (++guard > 12)
            {
                throw new InvalidOperationException($"Cannot resolve invalid local time {local:O} in {zone.Id}");
            }
        }

        return TimeZoneInfo.ConvertTimeToUtc(t, zone);
    }
}
