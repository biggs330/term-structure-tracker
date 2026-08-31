"""Standalone script: pull the standard 5-year commodity-market reference
window (INDUSTRY_LOOKBACK_YEARS in config.py) and print it.

Caveat: the earliest 3-4 years of this window still reflect these same 6
contracts when they were several years from delivery -- flatter than a
true regime signal. Read the recent ~1-2 years as reliable; the rest as
directional price-level context. See data.pull_curve_industry_window().
"""

import pandas as pd

from src.term_structure.data import pull_curve_industry_window

as_of = pd.Timestamp.today().normalize()
curve = pull_curve_industry_window(as_of)

print(f"Shape: {curve.shape}")
print(f"Range: {curve.index.min().date()} to {curve.index.max().date()}")
print(curve)
