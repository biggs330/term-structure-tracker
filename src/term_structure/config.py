from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

N_CONTRACTS = 6

# yfinance has no clean "CL1..CL6" continuous series beyond the front month
# (CL=F). Deferred contracts need explicit Yahoo contract symbols, e.g.
# "CLZ25.NYM" (month code + 2-digit year + .NYM). Month codes:
# F=Jan G=Feb H=Mar J=Apr K=May M=Jun N=Jul Q=Aug U=Sep V=Oct X=Nov Z=Dec.
# data.py needs to generate the next N_CONTRACTS month symbols from today's
# date and roll them forward as contracts expire.
MONTH_CODES = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z",
}

LOOKBACK_DAYS = 365
