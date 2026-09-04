using System;
using LionRegime.Core.Market;

namespace LionRegime.Core.Indicators;

/// <summary>
/// ATR по Уайлдеру. Инкрементальный: кормится закрытыми барами одного таймфрейма.
/// Первое значение = среднее первых Period значений True Range, дальше сглаживание Уайлдера.
/// Это тот же ATR, что рисует cTrader (ATR с MA type = Wilder Smoothing).
/// </summary>
public sealed class AtrCalculator
{
    private double _sum;
    private double _prevClose;
    private bool _hasPrevClose;

    public AtrCalculator(int period = 14)
    {
        if (period < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(period), "ATR period must be >= 1");
        }

        Period = period;
        Value = double.NaN;
    }

    public int Period { get; }

    /// <summary>NaN, пока не набралось Period баров.</summary>
    public double Value { get; private set; }

    public int BarsProcessed { get; private set; }

    public bool IsReady => !double.IsNaN(Value);

    public double OnBar(Bar bar)
    {
        var trueRange = _hasPrevClose
            ? Math.Max(bar.High - bar.Low, Math.Max(Math.Abs(bar.High - _prevClose), Math.Abs(bar.Low - _prevClose)))
            : bar.High - bar.Low;

        _prevClose = bar.Close;
        _hasPrevClose = true;
        BarsProcessed++;

        if (BarsProcessed < Period)
        {
            _sum += trueRange;
        }
        else if (BarsProcessed == Period)
        {
            _sum += trueRange;
            Value = _sum / Period;
        }
        else
        {
            Value = ((Value * (Period - 1)) + trueRange) / Period;
        }

        return Value;
    }
}
