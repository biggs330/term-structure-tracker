"""Standalone script: pull and print the full available history (~8 years)
for today's front-6 contracts, one batched call instead of six.

Caveat: early years reflect these same contracts when they were deeply
deferred (years from delivery) -- flat/meaningless as a regime signal that
far back. See data.pull_curve_long_history() docstring and README.
"""

import pandas as pd

from src.term_structure.data import pull_curve_long_history

as_of = pd.Timestamp.today().normalize()
curve = pull_curve_long_history(as_of)

print(f"Shape: {curve.shape}")
print(curve)
