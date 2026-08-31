import pandas as pd
import pytest

from src.term_structure import metrics


def test_slope_contango():
    curve = pd.DataFrame({"CL1": [70.0], "CL2": [71.0]})
    result = metrics.slope(curve)
    assert result.iloc[0] == pytest.approx((71.0 / 70.0 - 1) * 12)
    assert result.iloc[0] > 0


def test_slope_backwardation():
    curve = pd.DataFrame({"CL1": [70.0], "CL2": [69.0]})
    result = metrics.slope(curve)
    assert result.iloc[0] == pytest.approx((69.0 / 70.0 - 1) * 12)
    assert result.iloc[0] < 0


def test_regime_label_matches_slope_sign():
    slope_series = pd.Series([0.05, -0.05, 0.0])
    regime = metrics.regime_label(slope_series)
    assert list(regime) == ["contango", "backwardation", "backwardation"]


def test_roll_yield_front_two_matches_slope():
    curve = pd.DataFrame({
        "CL1": [70.0], "CL2": [71.0], "CL3": [72.0],
        "CL4": [73.0], "CL5": [74.0], "CL6": [75.0],
    })
    ry = metrics.roll_yield(curve)
    slope_result = metrics.slope(curve)
    assert ry["front_two"].iloc[0] == pytest.approx(slope_result.iloc[0])
    assert ry["full_curve"].iloc[0] == pytest.approx((75.0 / 70.0 - 1) * (12 / 5))
