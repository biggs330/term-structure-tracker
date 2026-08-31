"""Step 2: slope, annualized roll yield, and regime labeling."""

import numpy as np
import pandas as pd

from .config import N_CONTRACTS


def slope(curve: pd.DataFrame, months_between: float = 1.0) -> pd.Series:
    """(CL2/CL1 - 1) * (12 / months_between). Positive = contango.

    CL1/CL2 are always 1 calendar month apart by construction
    (contract_symbols() generates strictly consecutive months), so the
    default months_between=1.0 is correct for the standard front-two read.
    """
    return (curve["CL2"] / curve["CL1"] - 1) * (12 / months_between)


def roll_yield(curve: pd.DataFrame) -> pd.DataFrame:
    """Annualized roll yield, front-two vs. full-curve.

    front_two: CL2 vs CL1, same as slope() -- the standard, most liquid
        read of roll cost/benefit.
    full_curve: CL6 vs CL1, spread across all 6 months -- a broader read
        of overall curve steepness.
    """
    front_two = slope(curve)
    months_full = N_CONTRACTS - 1
    full_curve = (curve["CL6"] / curve["CL1"] - 1) * (12 / months_full)
    return pd.DataFrame({"front_two": front_two, "full_curve": full_curve})


def regime_label(slope_series: pd.Series) -> pd.Series:
    """Map slope sign to 'contango' / 'backwardation' per date."""
    return pd.Series(
        np.where(slope_series > 0, "contango", "backwardation"),
        index=slope_series.index,
        name="regime",
    )


def flip_dates(regime: pd.Series) -> pd.DatetimeIndex:
    """Dates where the regime differs from the previous day."""
    changed = regime != regime.shift()
    changed.iloc[0] = False  # first day is a start, not a flip
    return regime.index[changed]


def summarize_regimes(regime: pd.Series, slope_series: pd.Series) -> pd.DataFrame:
    """One row per regime streak: which regime, start/end, length, avg slope."""
    streak_id = (regime != regime.shift()).cumsum()
    rows = []
    for _, idx in regime.groupby(streak_id).groups.items():
        rows.append({
            "regime": regime.loc[idx].iloc[0],
            "start": idx[0],
            "end": idx[-1],
            "days": len(idx),
            "avg_slope_pct": slope_series.loc[idx].mean() * 100,
        })
    return pd.DataFrame(rows)


def one_line_label(regime: pd.Series, slope_series: pd.Series) -> str:
    """Human sentence: current regime, how long it's held, current slope."""
    streak_id = (regime != regime.shift()).cumsum()
    current_streak = streak_id.iloc[-1]
    streak_index = regime.index[streak_id == current_streak]

    current_regime = regime.iloc[-1]
    streak_start = streak_index[0]
    streak_days = len(streak_index)
    current_slope_pct = slope_series.iloc[-1] * 100

    return (
        f"WTI in {current_regime} since {streak_start.date()} "
        f"({streak_days} trading days), slope {current_slope_pct:+.1f}% annualized"
    )
