using System;
using System.Globalization;

namespace LionRegime.Core.Sessions;

/// <summary>High/Low одной сессии одного дня. Обновляется только закрытыми барами — lookahead исключён по построению.</summary>
public sealed class SessionRange
{
    public SessionRange(SessionWindow window)
    {
        Window = window ?? throw new ArgumentNullException(nameof(window));
        High = double.NaN;
        Low = double.NaN;
    }

    public SessionWindow Window { get; }

    public SessionTag Tag => Window.Tag;

    public double High { get; private set; }

    public double Low { get; private set; }

    public int BarCount { get; private set; }

    /// <summary>true после того, как пришёл бар с OpenTime ≥ EndUtc окна (или сессия сменилась днём).</summary>
    public bool IsComplete { get; private set; }

    public bool HasData => BarCount > 0;

    internal void AddBar(double high, double low)
    {
        if (IsComplete)
        {
            throw new InvalidOperationException($"{Window.Key} is already complete");
        }

        if (double.IsNaN(high) || double.IsNaN(low) || low > high)
        {
            throw new ArgumentException($"Invalid bar: high={high}, low={low}");
        }

        if (BarCount == 0)
        {
            High = high;
            Low = low;
        }
        else
        {
            if (high > High)
            {
                High = high;
            }

            if (low < Low)
            {
                Low = low;
            }
        }

        BarCount++;
    }

    internal void Complete() => IsComplete = true;

    public override string ToString() =>
        string.Format(CultureInfo.InvariantCulture, "{0} H={1} L={2} bars={3}{4}", Window.Key, High, Low, BarCount, IsComplete ? " done" : string.Empty);
}
