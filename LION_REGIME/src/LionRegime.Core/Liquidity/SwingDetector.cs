using System;
using System.Collections.Generic;
using LionRegime.Core.Market;

namespace LionRegime.Core.Liquidity;

/// <summary>
/// Фрактальные свинги. Period — полное окно (нечётное, по умолчанию 5): по (Period-1)/2 бара с каждой стороны.
///
/// Свинг подтверждается только когда закрылись все бары справа. Задержка подтверждения —
/// это не недостаток, а гарантия отсутствия lookahead: в реальном времени раньше знать нельзя.
/// </summary>
public sealed class SwingDetector
{
    private readonly List<Bar> _window = new List<Bar>();
    private readonly Timeframe _timeframe;

    public SwingDetector(Timeframe timeframe, int period = 5)
    {
        if (period < 3 || period % 2 == 0)
        {
            throw new ArgumentOutOfRangeException(nameof(period), "Swing period must be odd and >= 3");
        }

        _timeframe = timeframe;
        Period = period;
        Wing = (period - 1) / 2;
    }

    public int Period { get; }

    /// <summary>Сколько баров с каждой стороны от экстремума.</summary>
    public int Wing { get; }

    /// <summary>
    /// Подаёт закрытый бар. Возвращает свинги, подтверждённые ИМЕННО этим баром (0, 1 или 2 — хай и лой).
    /// </summary>
    public IReadOnlyList<Swing> OnBar(Bar bar)
    {
        _window.Add(bar);
        if (_window.Count > Period)
        {
            _window.RemoveAt(0);
        }

        if (_window.Count < Period)
        {
            return Array.Empty<Swing>();
        }

        var center = _window[Wing];
        var confirmedAt = Timeframes.CloseTimeOf(_timeframe, bar.OpenTimeUtc);
        List<Swing>? found = null;

        var isHigh = true;
        var isLow = true;
        for (var i = 0; i < Period; i++)
        {
            if (i == Wing)
            {
                continue;
            }

            if (_window[i].High >= center.High)
            {
                isHigh = false;
            }

            if (_window[i].Low <= center.Low)
            {
                isLow = false;
            }
        }

        if (isHigh)
        {
            (found ??= new List<Swing>()).Add(new Swing(PoolSide.High, center.High, center.OpenTimeUtc, confirmedAt, _timeframe));
        }

        if (isLow)
        {
            (found ??= new List<Swing>()).Add(new Swing(PoolSide.Low, center.Low, center.OpenTimeUtc, confirmedAt, _timeframe));
        }

        return (IReadOnlyList<Swing>?)found ?? Array.Empty<Swing>();
    }
}
