using LionRegime.Core.Sessions;

namespace LionRegime.Core.Tests.Sessions;

/// <summary>Хелперы тестов.</summary>
internal static class T
{
    public static DateTime Utc(int y, int mo, int d, int h, int mi) => new(y, mo, d, h, mi, 0, DateTimeKind.Utc);

    public static DateTime Date(int y, int mo, int d) => new(y, mo, d, 0, 0, 0, DateTimeKind.Unspecified);

    public static string Il(DateTime utc) => TimeZones.ToIsrael(utc).ToString("yyyy-MM-dd HH:mm");

    public static SessionWindow Window(SessionSchedule s, SessionTag tag, DateTime anchorLocalDate)
    {
        var def = s.Definitions.Single(d => d.Tag == tag);
        return def.WindowFor(anchorLocalDate) ?? throw new InvalidOperationException($"{tag} has no window on {anchorLocalDate:yyyy-MM-dd}");
    }
}
