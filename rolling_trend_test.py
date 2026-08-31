"""Standalone script: rolling/smoothed slope and regime, to see short-term
trend direction without single-day noise flipping the raw regime label.

Compares raw daily flips against a 5-day rolling-average version over the
1-year window -- see metrics.rolling_slope() / rolling_regime() docstrings.
"""

import pandas as pd

from src.term_structure.data import pull_curve
from src.term_structure.metrics import (
    flip_dates,
    regime_label,
    rolling_regime,
    rolling_slope,
    slope,
)

WINDOW = 5

curve = pull_curve(pd.Timestamp.today().normalize())
s = slope(curve)
regime = regime_label(s)

rs = rolling_slope(curve, window=WINDOW)
rregime = rolling_regime(curve, window=WINDOW).dropna()

print(f"Raw daily flips over the window:        {len(flip_dates(regime))}")
print(f"{WINDOW}-day rolling flips over the window:   {len(flip_dates(rregime))}")
print()

table = pd.DataFrame({
    "CL1": curve["CL1"],
    "raw_slope_pct": (s * 100).round(2),
    "raw_regime": regime,
    f"rolling{WINDOW}_slope_pct": (rs * 100).round(2),
    f"rolling{WINDOW}_regime": rregime,
})
pd.set_option("display.max_rows", 20)
pd.set_option("display.width", 140)
print(table.tail(20))
