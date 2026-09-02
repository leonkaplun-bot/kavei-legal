using System;
using System.Collections.Generic;

namespace LionRegime.Core.Sessions;

/// <summary>
/// Роли сессий для инструмента. Не влияет на расчёт High/Low — только на эффективный тег.
/// </summary>
public sealed class SessionProfile
{
    private readonly IReadOnlyDictionary<SessionTag, SessionRole> _roles;

    public SessionProfile(string name, IReadOnlyDictionary<SessionTag, SessionRole> roles)
    {
        Name = name ?? throw new ArgumentNullException(nameof(name));
        _roles = roles ?? throw new ArgumentNullException(nameof(roles));
    }

    /// <summary>FX-пары и индексы (GER40, EURUSD, GBPUSD): все сессии включены, LONDON — зона LION.</summary>
    public static SessionProfile Default { get; } = new SessionProfile(
        "DEFAULT",
        new Dictionary<SessionTag, SessionRole>
        {
            [SessionTag.LONDON] = SessionRole.Primary,
        });

    /// <summary>XAUUSD: главная — NY_CASH, LONDON — вторичная, ASIA — DEAD по умолчанию.</summary>
    public static SessionProfile Gold { get; } = new SessionProfile(
        "GOLD",
        new Dictionary<SessionTag, SessionRole>
        {
            [SessionTag.NY_CASH] = SessionRole.Primary,
            [SessionTag.LONDON] = SessionRole.Secondary,
            [SessionTag.ASIA] = SessionRole.Off,
        });

    public string Name { get; }

    /// <summary>Сессии, не упомянутые в профиле, — Secondary. DEAD всегда Off.</summary>
    public SessionRole RoleOf(SessionTag tag)
    {
        if (tag == SessionTag.DEAD)
        {
            return SessionRole.Off;
        }

        return _roles.TryGetValue(tag, out var role) ? role : SessionRole.Secondary;
    }

    /// <summary>Профиль по имени символа cTrader: XAU* → Gold, остальное → Default.</summary>
    public static SessionProfile ForSymbol(string symbol)
    {
        if (symbol is null)
        {
            throw new ArgumentNullException(nameof(symbol));
        }

        return symbol.IndexOf("XAU", StringComparison.OrdinalIgnoreCase) >= 0 ? Gold : Default;
    }

    public override string ToString() => Name;
}
