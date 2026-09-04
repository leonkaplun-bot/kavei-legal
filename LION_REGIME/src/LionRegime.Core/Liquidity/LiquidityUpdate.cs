using System;
using System.Collections.Generic;

namespace LionRegime.Core.Liquidity;

/// <summary>Что произошло на одном баре M5.</summary>
public sealed class LiquidityUpdate
{
    public static readonly LiquidityUpdate Empty =
        new LiquidityUpdate(Array.Empty<SweepEvent>(), Array.Empty<SweepEvent>(), Array.Empty<LiquidityPool>());

    public LiquidityUpdate(
        IReadOnlyList<SweepEvent> newSweeps,
        IReadOnlyList<SweepEvent> resolvedSweeps,
        IReadOnlyList<LiquidityPool> newPools)
    {
        NewSweeps = newSweeps ?? throw new ArgumentNullException(nameof(newSweeps));
        ResolvedSweeps = resolvedSweeps ?? throw new ArgumentNullException(nameof(resolvedSweeps));
        NewPools = newPools ?? throw new ArgumentNullException(nameof(newPools));
    }

    /// <summary>Пулы, снятые ЭТИМ баром. Возврат по ним, как правило, ещё не известен.</summary>
    public IReadOnlyList<SweepEvent> NewSweeps { get; }

    /// <summary>
    /// События, у которых на этом баре окончательно определился Reclaimed.
    /// Только их можно писать в CSV как готовые строки.
    /// </summary>
    public IReadOnlyList<SweepEvent> ResolvedSweeps { get; }

    public IReadOnlyList<LiquidityPool> NewPools { get; }

    public bool HasSweep => NewSweeps.Count > 0;
}
