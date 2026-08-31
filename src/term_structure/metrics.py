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


def rolling_slope(curve: pd.DataFrame, window: int = 5) -> pd.Series:
    """Moving average of daily slope() over `window` trading days.

    Raw daily slope flips sign on single-day noise when the curve is near
    flat (see README Interpretation: the choppy Sep-Dec 2025 stretch).
    Smoothing over a short window damps that noise while staying far more
    responsive than a monthly view -- reveals the underlying short-term
    trend direction instead of day-to-day flicker. Smaller window = more
    responsive/noisier, larger window = smoother/slower to react.
    """
    return slope(curve).rolling(window).mean()


def rolling_regime(curve: pd.DataFrame, window: int = 5) -> pd.Series:
    """regime_label() applied to rolling_slope() instead of raw daily slope."""
    return regime_label(rolling_slope(curve, window))


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


def monthly_summary(curve: pd.DataFrame) -> pd.DataFrame:
    """One row per calendar month: month-end CL1..CL6, slope, roll yield, regime.

    Resamples to month-end (last trading day of each month) rather than
    averaging the month -- standard convention for monthly price tables.
    Slope/roll yield/regime are recomputed on the monthly-resampled prices,
    not averaged from daily values, so they reflect the actual month-end
    curve shape.
    """
    monthly = curve.resample("ME").last().dropna(how="any")
    s = slope(monthly)
    ry = roll_yield(monthly)
    regime = regime_label(s)

    result = monthly.copy()
    result["slope_pct"] = (s * 100).round(2)
    result["roll_yield_full_pct"] = (ry["full_curve"] * 100).round(2)
    result["regime"] = regime
    return result


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
