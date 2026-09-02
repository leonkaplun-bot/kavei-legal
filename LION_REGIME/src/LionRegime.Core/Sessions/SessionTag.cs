namespace LionRegime.Core.Sessions;

/// <summary>
/// Тег сессии. Числовое значение = приоритет при пересечении окон: побеждает большее.
/// Пример: 09:00–10:00 Israel-summer активны и ASIA, и FRANKFURT → бар тегируется FRANKFURT,
/// но High/Low обеих сессий продолжают считаться.
/// </summary>
public enum SessionTag
{
    DEAD = 0,
    ASIA = 1,
    FRANKFURT = 2,
    LONDON = 3,
    NY_PRE = 4,
    NY_CASH = 5,
    LONDON_CLOSE = 6,
    NY_CLOSE = 7,
}
