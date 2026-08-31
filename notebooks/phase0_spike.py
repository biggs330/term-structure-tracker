"""Throwaway spike: does yfinance actually serve dated CL futures contracts?

Not part of the real pipeline. Just answering: can we pull CL2..CL6 as
distinct symbols, or only the continuous front-month CL=F?
"""

import yfinance as yf

CANDIDATES = [
    "CL=F",       # continuous front month, known to work, our baseline
    "CLV26.NYM",  # Oct 2026
    "CLX26.NYM",  # Nov 2026
    "CLZ26.NYM",  # Dec 2026
    "CLF27.NYM",  # Jan 2027
    "CLG27.NYM",  # Feb 2027
]

for symbol in CANDIDATES:
    print(f"\n--- {symbol} ---")
    try:
        df = yf.download(symbol, period="5d", progress=False)
        if df.empty:
            print("EMPTY (no data returned)")
        else:
            print(df.tail(3))
    except Exception as e:
        print(f"ERROR: {e}")
