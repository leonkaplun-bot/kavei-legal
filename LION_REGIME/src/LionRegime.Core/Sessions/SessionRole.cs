namespace LionRegime.Core.Sessions;

/// <summary>
/// Роль сессии для конкретного инструмента.
/// Off → бар получает тег DEAD, но High/Low этой сессии всё равно накапливаются
/// (Asia range нужен детектору режима и карте ликвидности даже там, где торговать нельзя).
/// </summary>
public enum SessionRole
{
    Off = 0,
    Secondary = 1,
    Primary = 2,
}
