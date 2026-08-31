"""Standalone script: monthly data table (one row per calendar month) over
the 5-year industry-standard window.

Each row is the month-end CL1..CL6 curve, plus slope/roll yield/regime
recomputed on those month-end prices. Same fixed-identity caveat as the
underlying pull applies -- older rows are less reliable as a regime signal
(see pull_curve_industry_window() docstring / README Known Limitations).
"""

import pandas as pd

from src.term_structure.data import pull_curve_industry_window
from src.term_structure.metrics import monthly_summary

curve = pull_curve_industry_window(pd.Timestamp.today().normalize())
table = monthly_summary(curve)

pd.set_option("display.max_rows", None)
pd.set_option("display.width", 140)
print(f"Shape: {table.shape}")
print(table)
