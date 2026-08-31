"""Step 1: pull CL1-CL6, align on date, drop missing.

Two ways to build the curve:
- pull_curve(): today's front 6 contracts, tracked by identity across the
  whole lookback window. Simple, but a contract's own price naturally
  converges as it nears expiry, which distorts a year-long spread history.
- pull_generic_curve(): the front 6 contracts *as of each individual date*,
  ranked by nearest-to-expiry. This is the correct basis for a regime
  history, since every date is measured on the same relative curve
  position (front month vs. 2nd month, etc.) rather than by fixed identity.
"""

from pathlib import Path

import pandas as pd
import yfinance as yf

from .config import DATA_PROCESSED, LOOKBACK_DAYS, MONTH_CODES, N_CONTRACTS


def _expiry(year: int, month: int) -> pd.Timestamp:
    """Approximate WTI last trading day: 3rd business day before the 25th
    of the month preceding delivery. Ignores exchange holidays."""
    prior_month, prior_year = (12, year - 1) if month == 1 else (month - 1, year)
    day = pd.Timestamp(year=prior_year, month=prior_month, day=25)
    business_days_back = 0
    while business_days_back < 3:
        day -= pd.Timedelta(days=1)
        if day.dayofweek < 5:  # Mon-Fri
            business_days_back += 1
    return day


def _next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _front_month(as_of: pd.Timestamp) -> tuple[int, int]:
    """(year, month) of the nearest contract that hasn't expired as of as_of."""
    as_of = pd.Timestamp(as_of)
    year, month = as_of.year, as_of.month
    while _expiry(year, month) < as_of:
        year, month = _next_month(year, month)
    return year, month


def _symbol_for(year: int, month: int) -> str:
    code = MONTH_CODES[month]
    yy = f"{year % 100:02d}"
    return f"CL{code}{yy}.NYM"


def contract_symbols(as_of: pd.Timestamp, n: int = N_CONTRACTS) -> list[str]:
    """Return the next `n` CL contract month symbols (front month first)."""
    year, month = _front_month(as_of)
    symbols = []
    for _ in range(n):
        symbols.append(_symbol_for(year, month))
        year, month = _next_month(year, month)
    return symbols


def _download_close(symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series | None:
    df = yf.download(symbol, start=start, end=end, progress=False)
    if df.empty:
        return None
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close


def _cache_path(as_of: pd.Timestamp) -> Path:
    return DATA_PROCESSED / f"curve_{as_of.date()}.parquet"


def pull_curve(as_of: pd.Timestamp | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Download daily settle for TODAY's CL1..CL6, tracked by identity.

    Returns a DataFrame indexed by date with columns CL1..CL6. Only valid
    for reading the *current* curve/slope -- see module docstring for why
    this is not a valid basis for a year-long regime history.

    Cached to data/processed/curve_<as_of date>.parquet so repeated runs
    for the same as_of don't re-hit yfinance. Pass use_cache=False to force
    a fresh pull (e.g. if you want the latest settle for today's date again).
    """
    if as_of is None:
        as_of = pd.Timestamp.today().normalize()
    else:
        as_of = pd.Timestamp(as_of)

    cache_path = _cache_path(as_of)
    if use_cache and cache_path.exists():
        return pd.read_parquet(cache_path)

    symbols = contract_symbols(as_of, N_CONTRACTS)
    start = as_of - pd.Timedelta(days=LOOKBACK_DAYS)
    end = as_of + pd.Timedelta(days=1)

    series = {}
    missing = []
    for i, symbol in enumerate(symbols, start=1):
        close = _download_close(symbol, start, end)
        if close is not None:
            series[f"CL{i}"] = close
        else:
            missing.append(symbol)

    if missing:
        raise RuntimeError(
            f"pull_curve(as_of={as_of.date()}) failed: {missing} returned no "
            f"data (likely already expired and delisted from Yahoo as of "
            f"today -- see README 'Known Limitations'). as_of must fall on "
            f"or after the date the current front-month contract itself "
            f"became front-month; going further back references contracts "
            f"that may have since expired. Try a more recent as_of."
        )

    curve = pd.DataFrame(series)
    curve.index.name = "date"
    curve = curve.dropna(how="any")

    if use_cache:
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        curve.to_parquet(cache_path)

    return curve


def pull_generic_curve(as_of: pd.Timestamp | None = None) -> pd.DataFrame:
    """Build the rolling/generic CL1..CL6 panel.

    For every date in the lookback window, ranks contracts by nearest-to-
    expiry (excluding anything already expired on that date) and assigns
    CL1..CL6 accordingly, so every row is measured on the same relative
    curve position regardless of which specific contracts were involved.

    KNOWN LIMITATION: Yahoo deletes price history for expired contracts
    entirely (confirmed by direct testing -- empty under every yfinance
    parameter combination, and absent from Yahoo's own search). Since most
    of a year-long window needs contracts that have since expired, this
    currently only returns ~1-2 weeks of real data, not a full year. Logic
    is correct and validated; it needs a data source with real historical
    coverage (e.g. a paid vendor) to be useful beyond that. See README
    "Known Limitations". pull_curve() is the current default for this
    reason.
    """
    if as_of is None:
        as_of = pd.Timestamp.today().normalize()
    else:
        as_of = pd.Timestamp(as_of)

    start = as_of - pd.Timedelta(days=LOOKBACK_DAYS)
    end = as_of + pd.Timedelta(days=1)

    earliest_front = _front_month(start)
    latest_far = _front_month(as_of)
    for _ in range(N_CONTRACTS - 1):
        latest_far = _next_month(*latest_far)

    months_needed = []
    year, month = earliest_front
    while (year, month) <= latest_far:
        months_needed.append((year, month))
        year, month = _next_month(year, month)

    prices: dict[str, pd.Series] = {}
    for year, month in months_needed:
        symbol = _symbol_for(year, month)
        close = _download_close(symbol, start, end)
        if close is not None:
            prices[symbol] = close

    all_dates = sorted(set().union(*(s.index for s in prices.values())))

    rows = {}
    for d in all_dates:
        if d < start or d > as_of:
            continue
        day_symbols = contract_symbols(d, N_CONTRACTS)
        row = {}
        complete = True
        for i, symbol in enumerate(day_symbols, start=1):
            series = prices.get(symbol)
            if series is None or d not in series.index:
                complete = False
                break
            row[f"CL{i}"] = series.loc[d]
        if complete:
            rows[d] = row

    curve = pd.DataFrame.from_dict(rows, orient="index")
    curve.index.name = "date"
    curve = curve.sort_index()
    return curve
