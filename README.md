# AT1 Stress Radar

A research and stress-testing prototype for Additional Tier 1 (AT1) bank
capital instruments.

> **Warning.** This project is a research prototype. It does not provide
> investment advice, executable prices, regulatory opinions, or definitive
> AT1 valuations. All included instrument data is synthetic.

## Purpose

AT1 instruments are perpetual, deeply subordinated bank capital securities
with issuer call options, coupon resets, discretionary coupons, and
contractual loss absorption. This project aims to help a user reason about
how an AT1 bond (and eventually a small portfolio) responds to interest-rate
changes, credit-spread changes, call versus extension assumptions, issuer
capital deterioration, and combined banking-sector stress.

## Current scope

The initial vertical slice can:

- Load a small synthetic AT1 instrument universe from YAML files.
- Validate instrument data with typed Pydantic models.
- Generate a contractual coupon schedule for a fixed-to-reset perpetual.
- Value two deterministic states with a flat discount rate:
  `called_at_first_call` and `extended_to_next_call`.
- Display terms, state values, and cash flows in a minimal Streamlit app.
- Validate a placeholder scenario file format for future stress work.

## Explicit non-goals (for now)

- No market data feeds, scraping, or Bloomberg/ECB/EBA integrations.
- No yield-curve engine or full bond-market conventions.
- No call-probability models, trigger-event probabilities, or ML.
- No portfolio analytics, persistence, authentication, or deployment.
- The scenario engine is a schema placeholder only; shocks are not yet applied.

## Repository structure

```
├── app/streamlit_app.py        # UI only; no domain logic
├── data/
│   ├── instruments/            # synthetic instrument YAML files
│   └── scenarios/              # placeholder scenario definitions
├── docs/                       # architecture, methodology, data dictionary
├── src/at1radar/
│   ├── domain/                 # Pydantic models (instruments, scenarios)
│   ├── data/                   # YAML loaders with validation
│   ├── cashflows/              # coupon schedule generation
│   ├── pricing/                # simplified state valuation
│   └── cli.py                  # validate / list-instruments / price
└── tests/                      # unit tests and YAML fixtures
```

## Installation

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Usage

Run everything from the repository root (the CLI defaults to
`data/instruments` relative to the working directory).

```bash
# Validate all instrument and scenario YAML files
uv run at1radar validate

# List the instrument universe
uv run at1radar list-instruments

# Value one instrument under the called and extended states
uv run at1radar price --instrument synthetic-alpha \
  --valuation-date 2025-06-30 --discount-rate 0.08 --reset-rate 0.03

# Launch the Streamlit app
uv run streamlit run app/streamlit_app.py
```

### Quality checks

```bash
uv run pytest                  # tests with coverage (fails under 80%)
uv run ruff format --check .   # formatting
uv run ruff check .            # linting
uv run mypy                    # type checking
```

### Python example

```python
from datetime import date

from at1radar.data.instrument_loader import load_instrument
from at1radar.domain.scenarios import CallState
from at1radar.pricing.state_pricing import value_both_states
from pathlib import Path

instrument = load_instrument(Path("data/instruments/synthetic_bank_alpha_at1.yaml"))
results = value_both_states(
    instrument=instrument,
    valuation_date=date(2025, 6, 30),
    flat_discount_rate=0.08,          # 8% flat annual discount rate
    assumed_reset_benchmark_rate=0.03,  # 3% benchmark assumed after reset
)
for state, result in results.items():
    print(state.value, result.terminal_date, f"{result.model_price_pct_of_notional:.2f}%")
```

## Conventions

- Rates are decimals throughout: `0.08` means 8%.
- Basis-point fields (`reset_margin_bps`, scenario `*_shock_bps`) are converted
  with `bps / 10_000`.

## Model limitations

- A single flat annual discount rate — no curve, no credit model.
- The reset benchmark is assumed constant after the first reset.
- Deterministic call states; no call-probability weighting.
- Coupon cancellation, trigger events, and write-down mechanics are recorded
  as terms but not modelled.
- No business-day adjustment; `ACT_ACT` is approximated as days / 365.25.
- Valuation dates before issue or on/after the first call date are out of scope.

See `docs/methodology.md` for details on why the outputs are model values,
not fair values.

## Planned next steps

1. Scenario engine: apply the placeholder scenario shocks (rates, spreads,
   reset rate, forced extension) to the state valuations and report a
   decomposition of the value change.
2. Multiple extension horizons (extend by N call periods, yield-to-worst
   style summary across call dates).
3. Simple credit-spread input separated from the risk-free rate.
