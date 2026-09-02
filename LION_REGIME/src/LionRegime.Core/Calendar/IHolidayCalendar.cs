using System;

namespace LionRegime.Core.Calendar;

/// <summary>
/// Праздники → SessionTag.DEAD. Источник (хардкод основных / CSV) — открытый вопрос №5 ТЗ.
/// В сессии 1 только интерфейс и пустая реализация.
/// </summary>
public interface IHolidayCalendar
{
    bool IsHoliday(DateTime utc);
}

/// <summary>Праздников нет. Дефолт, пока Leon не выбрал источник календаря.</summary>
public sealed class NoHolidays : IHolidayCalendar
{
    private NoHolidays()
    {
    }

    public static NoHolidays Instance { get; } = new NoHolidays();

    public bool IsHoliday(DateTime utc) => false;
}
