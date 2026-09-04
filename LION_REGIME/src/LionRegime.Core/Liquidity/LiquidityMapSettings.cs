using System;

namespace LionRegime.Core.Liquidity;

/// <summary>
/// Параметры карты ликвидности. Дефолты из ТЗ там, где они заданы; остальные выбраны в сессии 2
/// и помечены как «дефолт сессии 2» — их менять только с разрешения Leon'а.
/// </summary>
public sealed class LiquidityMapSettings
{
    /// <summary>Период ATR. ТЗ: 14.</summary>
    public int AtrPeriod { get; set; } = 14;

    /// <summary>Окно фрактала, нечётное. ТЗ: N = 5.</summary>
    public int SwingPeriod { get; set; } = 5;

    /// <summary>Допуск равенства хаёв/лоёв: k × ATR(14) своего TF. ТЗ: k = 0.15.</summary>
    public double EqToleranceAtr { get; set; } = 0.15;

    /// <summary>Сколько последних свингов TF просматривать при поиске кластера. Дефолт сессии 2.</summary>
    public int EqLookbackSwings { get; set; } = 20;

    /// <summary>
    /// Окно возврата после свипа, в барах M5. Дефолт сессии 2 = 6, согласован с условием
    /// режима DISTRIBUTION в ТЗ («последние N = 6 баров M5»). Бар свипа считается баром 0.
    /// </summary>
    public int ReclaimWithinBars { get; set; } = 6;

    /// <summary>
    /// Максимальное расстояние до цели в ATR(14, H1). Пулы дальше не попадают в TargetSet.
    /// Дефолт сессии 2 = 10. В ТЗ значение не задано.
    /// </summary>
    public double MaxDistanceAtr { get; set; } = 10.0;

    /// <summary>Сколько дней держать пулы в памяти. Больше месяца, чтобы PMH/PML доживали. Дефолт сессии 2.</summary>
    public int PoolRetentionDays { get; set; } = 90;

    public void Validate()
    {
        if (AtrPeriod < 1)
        {
            throw new InvalidOperationException("AtrPeriod must be >= 1");
        }

        if (SwingPeriod < 3 || SwingPeriod % 2 == 0)
        {
            throw new InvalidOperationException("SwingPeriod must be odd and >= 3");
        }

        if (EqToleranceAtr <= 0)
        {
            throw new InvalidOperationException("EqToleranceAtr must be > 0");
        }

        if (EqLookbackSwings < 2)
        {
            throw new InvalidOperationException("EqLookbackSwings must be >= 2");
        }

        if (ReclaimWithinBars < 0)
        {
            throw new InvalidOperationException("ReclaimWithinBars must be >= 0");
        }

        if (MaxDistanceAtr <= 0)
        {
            throw new InvalidOperationException("MaxDistanceAtr must be > 0");
        }

        if (PoolRetentionDays < 1)
        {
            throw new InvalidOperationException("PoolRetentionDays must be >= 1");
        }
    }
}
