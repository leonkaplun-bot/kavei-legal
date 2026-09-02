using System;
using System.Collections.Generic;

namespace LionRegime.Core.Sessions;

/// <summary>
/// Выход слоя 1 на каждый бар. Диапазоны (Current/Previous) — живые ссылки на объекты движка:
/// они меняются со следующими барами. Потребитель, которому нужен снимок, копирует значения сразу.
/// </summary>
public sealed class SessionState
{
    public SessionState(
        DateTime timeUtc,
        DateTime timeIsrael,
        SessionTag session,
        SessionTag windowTag,
        SessionRole role,
        int minutesIntoSession,
        bool isSessionOpen,
        bool isSessionClose,
        bool isHoliday,
        IReadOnlyDictionary<SessionTag, SessionRange> current,
        IReadOnlyDictionary<SessionTag, SessionRange> previous)
    {
        TimeUtc = timeUtc;
        TimeIsrael = timeIsrael;
        Session = session;
        WindowTag = windowTag;
        Role = role;
        MinutesIntoSession = minutesIntoSession;
        IsSessionOpen = isSessionOpen;
        IsSessionClose = isSessionClose;
        IsHoliday = isHoliday;
        Current = current ?? throw new ArgumentNullException(nameof(current));
        Previous = previous ?? throw new ArgumentNullException(nameof(previous));
    }

    public DateTime TimeUtc { get; }

    /// <summary>Только для отображения и колонки timestamp_il.</summary>
    public DateTime TimeIsrael { get; }

    /// <summary>Эффективный тег = окно × роль профиля × праздник. Это колонка session в CSV.</summary>
    public SessionTag Session { get; }

    /// <summary>Тег окна без учёта профиля и праздников (для отладки и LiquidityMap).</summary>
    public SessionTag WindowTag { get; }

    public SessionRole Role { get; }

    /// <summary>Минуты от начала окна WindowTag (см. SessionSlot.MinutesIntoSession).</summary>
    public int MinutesIntoSession { get; }

    public bool IsSessionOpen { get; }

    public bool IsSessionClose { get; }

    public bool IsHoliday { get; }

    public bool IsDead => Session == SessionTag.DEAD;

    /// <summary>Текущий (последний начатый) диапазон каждой сессии.</summary>
    public IReadOnlyDictionary<SessionTag, SessionRange> Current { get; }

    /// <summary>Предыдущий завершённый диапазон каждой сессии (для PDH/PDL-подобных сессионных пулов).</summary>
    public IReadOnlyDictionary<SessionTag, SessionRange> Previous { get; }

    public SessionRange? CurrentRange(SessionTag tag) => Current.TryGetValue(tag, out var range) ? range : null;

    public SessionRange? PreviousRange(SessionTag tag) => Previous.TryGetValue(tag, out var range) ? range : null;

    public override string ToString() => $"{TimeUtc:yyyy-MM-dd HH:mm}Z {Session} (+{MinutesIntoSession}m)";
}
