"""Standalone script: pull the curve and print slope/roll yield/regime."""

import pandas as pd

from src.term_structure.data import pull_curve
from src.term_structure.metrics import roll_yield, regime_label, slope

as_of = pd.Timestamp.today().normalize()

curve = pull_curve(as_of)
s = slope(curve)
ry = roll_yield(curve)
regime = regime_label(s)

print("=== Curve (last 5 rows) ===")
print(curve.tail())

print()
print("=== Today ===")
print(f"Slope (annualized):        {s.iloc[-1] * 100:.2f}%")
print(f"Roll yield (front-two):    {ry['front_two'].iloc[-1] * 100:.2f}%")
print(f"Roll yield (full-curve):   {ry['full_curve'].iloc[-1] * 100:.2f}%")
print(f"Regime:                    {regime.iloc[-1]}")

print()
print("=== Regime over the trailing year ===")
print(regime.value_counts())
print(f"Flips: {(regime != regime.shift()).sum() - 1}")
