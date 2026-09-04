using System;

namespace LionRegime.Core.Market;

/// <summary>Таймфреймы, которые нужны фазе 2. Значения совпадают по смыслу с cAlgo TimeFrame.</summary>
public enum Timeframe
{
    M5,
    H1,
    H4,
    D1,
    W1,
    MN1,
}

public static class Timeframes
{
    /// <summary>
    /// Время закрытия бара = момент, когда бар становится ИЗВЕСТЕН.
    /// Это и есть CreatedAt для пулов, построенных на этом баре: раньше него пул использовать нельзя.
    /// MN1 считается по календарю, а не фиксированной длительностью.
    /// </summary>
    public static DateTime CloseTimeOf(Timeframe tf, DateTime openTimeUtc)
    {
        var t = Sessions.TimeZones.EnsureUtc(openTimeUtc);
        switch (tf)
        {
            case Timeframe.M5:
                return t.AddMinutes(5);
            case Timeframe.H1:
                return t.AddHours(1);
            case Timeframe.H4:
                return t.AddHours(4);
            case Timeframe.D1:
                return t.AddDays(1);
            case Timeframe.W1:
                return t.AddDays(7);
            case Timeframe.MN1:
                return new DateTime(t.Year, t.Month, 1, 0, 0, 0, DateTimeKind.Utc).AddMonths(1);
            default:
                throw new ArgumentOutOfRangeException(nameof(tf), tf, "Unknown timeframe");
        }
    }
}
