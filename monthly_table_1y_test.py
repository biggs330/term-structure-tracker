"""Standalone script: monthly data table (one row per calendar month) over
the 1-year default window (data.pull_curve()).

Each row is the month-end CL1..CL6 curve, plus slope/roll yield/regime
recomputed on those month-end prices. This is the most reliable of the
three monthly tables -- least affected by the fixed-identity caveat, since
these contracts weren't yet deep-deferred a year ago.
"""

import pandas as pd

from src.term_structure.data import pull_curve
from src.term_structure.metrics import monthly_summary

curve = pull_curve(pd.Timestamp.today().normalize())
table = monthly_summary(curve)

pd.set_option("display.max_rows", None)
pd.set_option("display.width", 140)
print(f"Shape: {table.shape}")
print(table)
