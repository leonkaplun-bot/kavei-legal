using System;
using System.Globalization;

namespace LionRegime.Core.Market;

/// <summary>
/// Закрытый бар. Время — момент ОТКРЫТИЯ бара в UTC (cAlgo: Bars.OpenTimes[i]).
/// Только закрытые бары: незакрытый бар в карту ликвидности не попадает никогда.
/// </summary>
public readonly struct Bar : IEquatable<Bar>
{
    public Bar(DateTime openTimeUtc, double open, double high, double low, double close)
    {
        if (double.IsNaN(open) || double.IsNaN(high) || double.IsNaN(low) || double.IsNaN(close))
        {
            throw new ArgumentException("Bar prices must not be NaN");
        }

        if (low > high)
        {
            throw new ArgumentException($"Low {low} must not exceed high {high}", nameof(low));
        }

        if (open < low || open > high || close < low || close > high)
        {
            throw new ArgumentException($"Open {open} and close {close} must lie within [{low}, {high}]");
        }

        OpenTimeUtc = Sessions.TimeZones.EnsureUtc(openTimeUtc);
        Open = open;
        High = high;
        Low = low;
        Close = close;
    }

    public DateTime OpenTimeUtc { get; }

    public double Open { get; }

    public double High { get; }

    public double Low { get; }

    public double Close { get; }

    public double Range => High - Low;

    public bool Equals(Bar other) =>
        OpenTimeUtc == other.OpenTimeUtc &&
        Open.Equals(other.Open) &&
        High.Equals(other.High) &&
        Low.Equals(other.Low) &&
        Close.Equals(other.Close);

    public override bool Equals(object? obj) => obj is Bar other && Equals(other);

    public override int GetHashCode() => HashCode.Combine(OpenTimeUtc, Open, High, Low, Close);

    public override string ToString() =>
        string.Format(CultureInfo.InvariantCulture, "{0:yyyy-MM-dd HH:mm}Z O={1} H={2} L={3} C={4}", OpenTimeUtc, Open, High, Low, Close);
}
