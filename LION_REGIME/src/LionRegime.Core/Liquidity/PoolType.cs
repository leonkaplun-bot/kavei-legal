namespace LionRegime.Core.Liquidity;

/// <summary>
/// Тип пула ликвидности. Имена совпадают с ТЗ и попадают в CSV как есть.
/// </summary>
public enum PoolType
{
    /// <summary>Previous day high / low.</summary>
    PDH,
    PDL,

    /// <summary>Previous week high / low.</summary>
    PWH,
    PWL,

    /// <summary>Previous month high / low.</summary>
    PMH,
    PML,

    ASIA_H,
    ASIA_L,
    LONDON_H,
    LONDON_L,

    /// <summary>Сессия NY_CASH.</summary>
    NY_H,
    NY_L,

    /// <summary>Equal highs / lows: кластер из >= 2 свингов в пределах допуска.</summary>
    EQH,
    EQL,

    /// <summary>Фрактальный свинг.</summary>
    SWING_H,
    SWING_L,
}

/// <summary>Сторона пула. Определяет, чем его снимают: хаем бара или лоем.</summary>
public enum PoolSide
{
    High,
    Low,
}

public static class PoolTypes
{
    public static PoolSide SideOf(PoolType type)
    {
        switch (type)
        {
            case PoolType.PDH:
            case PoolType.PWH:
            case PoolType.PMH:
            case PoolType.ASIA_H:
            case PoolType.LONDON_H:
            case PoolType.NY_H:
            case PoolType.EQH:
            case PoolType.SWING_H:
                return PoolSide.High;
            default:
                return PoolSide.Low;
        }
    }

    public static bool IsHigh(PoolType type) => SideOf(type) == PoolSide.High;
}
