namespace LionRegime.Core.Liquidity;

/// <summary>
/// Направление поиска целей. Long — цели ВЫШЕ цены, Short — НИЖЕ.
/// Слой 2 ничего не торгует: это просто сторона, в которую смотрим.
/// </summary>
public enum TradeDirection
{
    Long,
    Short,
}
