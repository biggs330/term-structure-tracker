# Term-Structure Tracker

**Question:** Is WTI in contango or backwardation today, and how has that flipped over the last year?

## Data
Front 6 CL (WTI) contracts, daily settle, pulled via `yfinance`.

**Scope note:** the year-long trend uses `data.pull_curve()` — today's 6
contracts tracked by fixed identity across the lookback window, not a true
generic/rolling front-month series. See "Known Limitations" below for why,
and treat the historical trend as approximate/directional, not precise.

## Method

**Variables:** `CLi,t` = settle price of the i-th nearest-to-expiry contract on date `t`.

**1. Contract expiry (roll-date rule)**
```
Expiry(Y, M) = 3rd business day before the 25th calendar day of month (M-1)
```
(year rolls back one if M = January)

**2. Front month selection**
```
FrontMonth(t) = smallest (Y, M) such that Expiry(Y, M) >= t
```

**3. Slope (annualized, front-two)**
```
Slope_t = (CL2,t / CL1,t - 1) * (12 / months_between)
```
`months_between = 1` always, since CL1/CL2 are constructed to be exactly
one calendar month apart. Positive -> contango, negative -> backwardation.

**4. Roll yield, front-two** -- identical to Slope_t above.

**5. Roll yield, full-curve**
```
RollYield_full,t = (CL6,t / CL1,t - 1) * (12 / 5)
```
(5 = number of months spanned from CL1 to CL6)

**6. Regime label**
```
Regime_t = contango       if Slope_t > 0
           backwardation  otherwise
```

**7. Regime streak average**
```
AvgSlope_streak = mean(Slope_t for all t in that contiguous streak)
```

**Verification:** cross-checked three ways -- direct source read, hand
recomputation against live data bypassing `metrics.py` entirely (exact
float match), and a from-scratch reimplementation of the expiry-date rule
in plain `datetime` (matches on all tested cases, including the January
year-wrap boundary). See `tests/test_data.py` and `tests/test_metrics.py`
for the automated versions of these checks.

## Deliverable
Animated curve + a one-line regime label, posted to `#journalclub` on
Discord for the weekly meeting.

## Week-One Steps
1. Pull CL1–CL6 with `yfinance`, align on date, drop missing.
2. Slope = `(CL2/CL1 − 1) × (12 / months_between)`. Positive = contango.
3. Shade regimes on a price chart.

## Project Layout
```
src/term_structure/
    config.py       # constants: N_CONTRACTS, LOOKBACK_DAYS, paths, month codes
    data.py         # pull + align CL1-CL6, roll-date logic, parquet caching
    metrics.py      # slope, roll yield, regime labeling, streak summary
    viz.py          # regime-shaded chart + animated curve
    pipeline.py     # glue: run end-to-end, save all outputs
    notify.py       # post chart/animation/label to Discord #journalclub
data/
    raw/            # reserved, currently unused
    processed/      # pull_curve()/pull_curve_long_history()'s parquet caches, gitignored
outputs/            # regime_chart.png, curve_animation.gif, label.txt, gitignored
notebooks/          # phase0_spike.py -- disposable yfinance validation script
tests/
    test_data.py    # roll-date / expiry / contract_symbols logic
    test_metrics.py # slope / roll yield / regime math
pull_test.py               # standalone: just pull and print the curve
pull_long_history_test.py  # standalone: pull ~8yr history, one batched call
metrics_test.py            # standalone: pull + print slope/roll yield/regime
post_to_discord.py         # standalone: post the latest outputs to Discord (run manually)
.env.example                # template for the required DISCORD_WEBHOOK_URL
```

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Manually Running Things

**Full pipeline** (pull data, compute metrics, generate chart + animation +
label, save everything to `outputs/`):
```bash
python -m src.term_structure.pipeline
```

**Just check the raw data pull**, no metrics or charts:
```bash
python pull_test.py
```

**Data + slope/roll yield/regime**, printed to the terminal, no charts:
```bash
python metrics_test.py
```

**Full available history (~8 years) for today's front-6 contracts**, one
batched multi-ticker call instead of six separate ones. Caveat: early years
reflect these same contracts when they were deeply deferred from delivery,
so spreads are naturally flat and not a meaningful regime signal that far
back -- useful for eyeballing long-run price levels only. See
`data.pull_curve_long_history()` docstring.
```bash
python pull_long_history_test.py
```

**Post the latest outputs to Discord** (requires `DISCORD_WEBHOOK_URL` set
in a local `.env` file — copy `.env.example` and fill in your real webhook
URL from Discord's Server Settings -> Integrations -> Webhooks). This is
never run automatically — you run it yourself when you're ready to post:
```bash
python post_to_discord.py
```

**Run the test suite** (fast, no network calls, no yfinance dependency):
```bash
python -m pytest tests/ -v
```

There is no automated scheduling (cron/launchd) -- by design, everything
above is run manually, on demand.

## Adjusting Parameters

Everything tunable lives in `src/term_structure/config.py`:

| Constant | Meaning | Notes |
|---|---|---|
| `N_CONTRACTS` | How many contracts make up the curve | Default 6 (CL1..CL6). Changing this changes column names everywhere and `roll_yield()`'s full-curve month divisor (`N_CONTRACTS - 1`) -- both update automatically. |
| `LOOKBACK_DAYS` | How far back `pull_curve()` pulls history | Default 365. Larger values mean more data per pull (slower, more yfinance calls) but don't fix the historical-accuracy issue described in Known Limitations -- that's a data-availability wall, not a lookback setting. |
| `MONTH_CODES` | CL contract month-letter mapping | Standard futures month codes (F=Jan .. Z=Dec). Don't change -- this is a fixed industry convention, not a tunable. |
| `DATA_PROCESSED` / `OUTPUTS` | Where cache files / chart-animation-label outputs get written | Change if you want a different folder layout. |

**Other things you can adjust directly in code:**
- `viz.animate_curve(curve, out_path, stride=5)` -- `stride` controls how
  many days are skipped between animation frames. Lower = smoother/longer
  GIF, higher = choppier/shorter. Default samples roughly weekly.
- `metrics.roll_yield()` -- currently reports both `front_two` (CL2 vs CL1)
  and `full_curve` (CL6 vs CL1). Add a middle-of-curve variant here if you
  want a third read.
- `viz.REGIME_COLORS` -- the contango/backwardation shading colors on the
  static chart.

## Backtesting / Running Against a Different Date

`pull_curve()` accepts a custom `as_of` date instead of today:
```python
from src.term_structure.data import pull_curve
import pandas as pd

curve = pull_curve(pd.Timestamp("2026-08-24"), use_cache=False)
```

**This only works within the current roll cycle** -- `as_of` must fall on
or after the date the *current* front-month contract itself became the
front month. Going further back references a contract that has, by today,
already expired and been purged from Yahoo (see Known Limitations). As of
this writing that's roughly the last 1-2 weeks; the exact boundary moves
forward every time the front month rolls (about monthly).

If `as_of` goes back too far, `pull_curve()` raises a clear `RuntimeError`
naming exactly which symbol failed and why, instead of silently returning
a curve with a missing/mislabeled column -- an earlier version of this
function had that exact bug (a too-old `as_of` would silently drop CL1
and shift the remaining columns without renaming them), caught by directly
testing this boundary before writing these instructions.

**This is not a general backtesting engine.** There's no way, with the
current free data source, to test the pipeline against an arbitrary past
date (a month ago, a year ago, the April 2020 negative-WTI event) --
that data is gone from Yahoo. The metrics math itself is instead validated
with hand-computed unit tests (`tests/test_metrics.py`), not live historical
data. See "Known Limitations" for the full explanation and the path to a
real fix (swapping in a paid data vendor for `pull_generic_curve()`).

## Known Limitations

**yfinance/Yahoo does not retain price history for expired CL contracts.**
Once a futures contract passes its last trading day, Yahoo Finance deletes
it from their system entirely — not just future dates, the whole history.
Confirmed by direct testing (2026-08-31):
- `yf.download()` / `yf.Ticker().history()` on an expired symbol (e.g.
  `CLU26.NYM`, expired ~1 week prior) return empty under every parameter
  combination tried (`auto_adjust`, `repair=True`, plain vs. `Adj Close`).
- Yahoo's own search/lookup API returns zero results for the same symbol.
- 8 alternate symbol formats tested, all empty.
- `Ticker().fast_info` errors out — Yahoo has no metadata for the symbol
  at all, not even currency.

**Why this matters:** a proper "how has the regime flipped over the last
year" answer requires a *generic/rolling* front-month series — for each
historical date, rank contracts by nearest-to-expiry and assign CL1..CL6
accordingly (see `data.pull_generic_curve()`). That function is built and
logically correct (validated against Phase 0's roll-date math), but it
can only produce ~1-2 weeks of real data before running into contracts
that have since expired and are no longer downloadable. It cannot cover
a full year with this data source.

**Free alternatives checked and ruled out:**
- EIA's generic contract-1-4 series (`RCLC1`-`RCLC4`) — discontinued
  after 2024-04-05.
- Quandl/Nasdaq Data Link CHRIS database — deprecated, no longer updated.
- CME Group's public settlement pages — manual, one-date-at-a-time,
  no bulk download or free API (their real API product, CME DataMine,
  is a paid enterprise product).
- TurtleTrader (turtletrader.com/hpd) — correct per-contract file
  structure, but the entire archive stopped updating in October 2002.

**Current decision:** scope narrowed to `pull_curve()` (fixed-identity,
today's 6 contracts tracked across the year). This gives an accurate
*current* slope/regime reading, but the year-long trend it produces is
distorted by contracts naturally converging as they approach their own
expiry (a real futures-market effect, sometimes called the Samuelson
effect), independent of actual regime changes. Treat the historical
animation as directional, not precise.

**If this needs to be fixed properly later:** `pull_generic_curve()` is
already implemented correctly — it just needs a paid data source (e.g.
Databento) swapped in for the `yf.download()` calls, since the ranking
and roll-date logic itself doesn't need to change.

**Corollary: `pull_curve()` only works for `as_of` close to today.** See
"Backtesting / Running Against a Different Date" above for the precise
boundary and the clear error it now raises when `as_of` goes back too far.

## Interpretation (snapshot as of 2026-08-31)

Reading the current output, `regime_chart.png`: the year splits into two
distinct stretches.

**Sep–Dec 2025: choppy, flipping between contango and backwardation.**
The regime streaks in this stretch have tiny average slopes (roughly
±0.3–0.7% annualized — see `metrics.summarize_regimes()` output). When the
underlying spread is genuinely close to zero, the regime label (a hard cutoff
at slope = 0) flips on small day-to-day noise even though the market isn't
dramatically changing its mind. This is a normal state: storage economics
roughly balanced, no strong directional signal.

**Dec 2025–present: one long, deepening backwardation streak.** Over the
same window, front-month price rallied from ~$57 to ~$86/bbl. Backwardation
paired with a rising front-month price is the classic signature of prompt
supply tightening (or demand outpacing it) faster than the market expects
further out the curve — traders are paying up for oil *now* relative to
later. Physical tightness like this doesn't resolve in a day; it takes time
for new supply to come online, inventories to rebuild, or high prices to
destroy demand. So a backwardation regime persisting for months, once it's
real, is expected — it's a sticky physical imbalance, not a coin-flip curve.

**Caveat (ties back to Known Limitations above):** some of this stretch's
length and steepness is a genuine market signal, and some of it is the fixed-
contract convergence artifact — these same six contracts naturally widen in
spread as they approach their own expiry, independent of fundamentals. We
can't cleanly separate the two with the current free data source. Read this
as: **the direction (backwardation, since ~Dec 2025) is solid; the precise
magnitude and exact duration should be presented with the caveat attached.**
