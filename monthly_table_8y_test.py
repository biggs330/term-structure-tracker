"""Standalone script: monthly data table (one row per calendar month) over
the full ~8-year available window (data.pull_curve_long_history()).

Each row is the month-end CL1..CL6 curve, plus slope/roll yield/regime
recomputed on those month-end prices. Least reliable of the three monthly
tables for regime reading -- the earliest years reflect these same 6
contracts when they were deeply deferred from delivery (see
pull_curve_long_history() docstring / README Known Limitations). Useful
for long-run month-end price-level context, not precise regime history.
"""

import pandas as pd

from src.term_structure.data import pull_curve_long_history
from src.term_structure.metrics import monthly_summary

curve = pull_curve_long_history(pd.Timestamp.today().normalize())
table = monthly_summary(curve)

pd.set_option("display.max_rows", None)
pd.set_option("display.width", 140)
print(f"Shape: {table.shape}")
print(table)
