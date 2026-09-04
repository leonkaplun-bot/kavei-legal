using System;
using System.Globalization;
using LionRegime.Core.Market;

namespace LionRegime.Core.Liquidity;

/// <summary>Подтверждённый фрактальный свинг.</summary>
public readonly struct Swing
{
    public Swing(PoolSide side, double price, DateTime occurredAt, DateTime confirmedAt, Timeframe timeframe)
    {
        Side = side;
        Price = price;
        OccurredAt = occurredAt;
        ConfirmedAt = confirmedAt;
        Timeframe = timeframe;
    }

    public PoolSide Side { get; }

    public double Price { get; }

    /// <summary>Время открытия бара-экстремума.</summary>
    public DateTime OccurredAt { get; }

    /// <summary>
    /// Время, когда свинг стал ИЗВЕСТЕН: закрытие последнего подтверждающего бара справа.
    /// Всегда позже OccurredAt. Именно это идёт в CreatedAt пула — иначе получился бы lookahead.
    /// </summary>
    public DateTime ConfirmedAt { get; }

    public Timeframe Timeframe { get; }

    public override string ToString() =>
        string.Format(CultureInfo.InvariantCulture, "{0} {1} @{2} ({3:yyyy-MM-dd HH:mm}Z, confirmed {4:yyyy-MM-dd HH:mm}Z)", Timeframe, Side, Price, OccurredAt, ConfirmedAt);
}
