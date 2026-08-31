"""Standalone script that does nothing but pull the CL curve data and print it."""

import pandas as pd

from src.term_structure.data import pull_curve, pull_generic_curve

as_of = pd.Timestamp.today().normalize()

print("=== pull_curve (fixed contracts) ===")
curve = pull_curve(as_of)
print(curve)

print()
print("=== pull_generic_curve (rolling/generic) ===")
generic = pull_generic_curve(as_of)
print(generic)
