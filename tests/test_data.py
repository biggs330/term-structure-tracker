import pandas as pd

from src.term_structure.data import _expiry, _front_month, _next_month, contract_symbols


def test_expiry_third_business_day_before_25th():
    # October 2026 delivery -> expiry in September 2026.
    # Sep 25, 2026 is a Friday; 3 business days back: Sep24(Thu), Sep23(Wed), Sep22(Tue).
    assert _expiry(2026, 10) == pd.Timestamp("2026-09-22")


def test_expiry_handles_january_wrapping_to_prior_december():
    # January 2026 delivery -> expiry in December 2025.
    assert _expiry(2026, 1) == pd.Timestamp("2025-12-22")


def test_next_month_rolls_december_to_next_january():
    assert _next_month(2026, 12) == (2027, 1)


def test_next_month_normal_case():
    assert _next_month(2026, 8) == (2026, 9)


def test_front_month_matches_phase0_validated_case():
    # Confirmed against real yfinance data in Phase 0: CL=F == CLV26.NYM on this date.
    assert _front_month(pd.Timestamp("2026-08-31")) == (2026, 10)


def test_front_month_still_valid_on_its_own_expiry_day():
    assert _front_month(pd.Timestamp("2026-09-22")) == (2026, 10)


def test_front_month_rolls_the_day_after_expiry():
    assert _front_month(pd.Timestamp("2026-09-23")) == (2026, 11)


def test_contract_symbols_matches_phase1_validated_output():
    symbols = contract_symbols(pd.Timestamp("2026-08-31"))
    assert symbols == [
        "CLV26.NYM", "CLX26.NYM", "CLZ26.NYM",
        "CLF27.NYM", "CLG27.NYM", "CLH27.NYM",
    ]


def test_contract_symbols_respects_n():
    symbols = contract_symbols(pd.Timestamp("2026-08-31"), n=3)
    assert symbols == ["CLV26.NYM", "CLX26.NYM", "CLZ26.NYM"]


def test_contract_symbols_are_consecutive_months():
    # Downstream slope() math assumes CL1/CL2 are always 1 month apart.
    symbols = contract_symbols(pd.Timestamp("2026-08-31"))
    months = [s[2] for s in symbols]  # month code is always the 3rd character
    from src.term_structure.config import MONTH_CODES
    code_order = list(MONTH_CODES.values())
    positions = [code_order.index(m) for m in months]
    diffs = [(positions[i + 1] - positions[i]) % 12 for i in range(len(positions) - 1)]
    assert all(d == 1 for d in diffs)
