using System;
using System.Collections.Generic;

namespace LionRegime.Core.Sessions;

/// <summary>Результат классификации момента времени расписанием: без состояния, без профиля, без праздников.</summary>
public sealed class SessionSlot
{
    public SessionSlot(
        DateTime timeUtc,
        SessionTag tag,
        SessionWindow? window,
        int minutesIntoSession,
        bool isSessionOpen,
        bool isSessionClose,
        IReadOnlyList<SessionWindow> activeWindows)
    {
        TimeUtc = timeUtc;
        Tag = tag;
        Window = window;
        MinutesIntoSession = minutesIntoSession;
        IsSessionOpen = isSessionOpen;
        IsSessionClose = isSessionClose;
        ActiveWindows = activeWindows ?? throw new ArgumentNullException(nameof(activeWindows));
    }

    public DateTime TimeUtc { get; }

    /// <summary>Тег окна с наивысшим приоритетом; DEAD, если ни одно окно не активно.</summary>
    public SessionTag Tag { get; }

    /// <summary>Окно-победитель; null для DEAD.</summary>
    public SessionWindow? Window { get; }

    /// <summary>
    /// Минуты от начала окна. Для DEAD — минуты с конца последнего завершившегося окна
    /// (-1, если в пределах недели назад окон не было).
    /// </summary>
    public int MinutesIntoSession { get; }

    /// <summary>Первые N минут окна (N = SessionSchedule.OpenWindowMinutes).</summary>
    public bool IsSessionOpen { get; }

    /// <summary>Последние N минут окна (N = SessionSchedule.CloseWindowMinutes).</summary>
    public bool IsSessionClose { get; }

    /// <summary>Все окна, содержащие момент (пересечения), по возрастанию приоритета. Последнее = Window.</summary>
    public IReadOnlyList<SessionWindow> ActiveWindows { get; }

    public bool IsDead => Tag == SessionTag.DEAD;

    public override string ToString() => $"{TimeUtc:yyyy-MM-dd HH:mm}Z {Tag} +{MinutesIntoSession}m";
}
