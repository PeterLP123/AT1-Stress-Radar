# AT1 Stress Radar

[![CI](https://github.com/PeterLP123/AT1-Stress-Radar/actions/workflows/ci.yml/badge.svg)](https://github.com/PeterLP123/AT1-Stress-Radar/actions/workflows/ci.yml)

An explainable research workbench for Additional Tier 1 (AT1) call, extension,
and capital-stress analysis.

AT1 instruments combine perpetual maturity, issuer call options, coupon resets,
discretionary distributions, and contractual loss absorption. The project aims
to make each assumption and cash flow inspectable instead of hiding them behind
a single model price.

> **Research prototype.** The current model does not provide investment advice,
> executable prices, regulatory opinions, or definitive AT1 valuations. All
> instrument data shipped with the repository is synthetic.

## Current status

Version `0.1.0` answers one deliberately narrow question: how does a synthetic
AT1's model value change if it is called at the first call date or extended to
the next call date?

| Capability | Status |
|---|---|
| Typed instrument terms and defensive YAML validation | Working |
| Issue-anchored fixed-to-reset coupon schedules | Working |
| Called and one-period-extended state values | Working |
| CLI and local Streamlit interface | Working |
| Scenario definitions | Validated only; shocks are not applied yet |
| Curves, issuer capital data, loss absorption, portfolios, and live data | Not implemented |

The intended destination is an evidence-linked **extension and capital-action
risk radar**, not another opaque bond-price calculator. See the
[roadmap](docs/roadmap.md) for the product thesis and milestone gates.

## Quick start

You need Python 3.12 and [uv](https://docs.astral.sh/uv/). Run commands from
the repository root because the CLI's sample-data paths are working-directory
relative.

```bash
uv sync --locked
uv run at1radar validate
uv run at1radar list-instruments
```

Price the sample Alpha instrument under both supported call states:

```bash
uv run at1radar price \
  --instrument synthetic-alpha \
  --valuation-date 2025-06-30 \
  --discount-rate 0.08 \
  --reset-rate 0.03
```

The final lines should look like this:

```text
  called_at_first_call     terminal 2027-03-15  PV     199,557.07 EUR  price   99.779% of notional  (4 cash flows)
  extended_to_next_call    terminal 2032-03-15  PV     197,084.33 EUR  price   98.542% of notional  (14 cash flows)
```

Launch the local interface:

```bash
uv run streamlit run app/streamlit_app.py
```

The app lets you inspect terms, change valuation assumptions, compare the two
states, and audit every generated cash flow.

## Use as a Python package

```python
from datetime import date
from pathlib import Path

from at1radar.data.instrument_loader import load_instrument
from at1radar.pricing.state_pricing import value_both_states

instrument = load_instrument(
    Path("data/instruments/synthetic_bank_alpha_at1.yaml")
)
results = value_both_states(
    instrument=instrument,
    valuation_date=date(2025, 6, 30),
    flat_discount_rate=0.08,
    assumed_reset_benchmark_rate=0.03,
)

for state, result in results.items():
    print(
        state.value,
        result.terminal_date,
        f"{result.model_price_pct_of_notional:.2f}%",
    )
```

## Model boundary

The current engine generates contractual cash flows and discounts them at a
single flat annual rate. Post-reset coupons use a constant assumed benchmark
plus the contractual reset margin. It supports `ACT_365`, an approximate
`ACT_ACT`, and US `THIRTY_360` accrual.

It does **not** currently model:

- separate risk-free curves and credit spreads;
- call probabilities or more than one extension horizon;
- coupon cancellation, maximum distributable amount (MDA) restrictions, CET1
  trigger events, write-down, or equity conversion;
- settlement, accrued interest, business-day adjustment, or post-first-call
  valuation;
- real instrument terms, issuer fundamentals, market prices, persistence, or
  authentication.

The outputs are simplified state values for relative sensitivity analysis,
not fair values. The [methodology](docs/methodology.md) records the equations,
conventions, and consequences of each simplification.

## Data conventions

- Rates are decimals: `0.08` means 8%.
- Basis-point fields use quoted bps: `450` means 450 bps. Scenario shocks are
  not converted or applied until the scenario engine is implemented.
- Dates use ISO `YYYY-MM-DD`.
- Every bundled instrument sets `is_synthetic: true` and records its source
  and verification date.

See the [data dictionary](docs/data_dictionary.md) before adding an instrument
or scenario. Validate changes with `uv run at1radar validate`.

## Repository map

```text
app/streamlit_app.py        local user interface
data/instruments/           synthetic instrument YAML
data/scenarios/             starting scenario definitions
docs/                       architecture, methodology, data reference, roadmap
src/at1radar/domain/        validated instruments and scenario types
src/at1radar/data/          defensive YAML loaders
src/at1radar/cashflows/     coupon schedule generation
src/at1radar/pricing/       deterministic state valuation
src/at1radar/cli.py         validate, list-instruments, and price commands
tests/                      unit, boundary, loader, and CLI tests
```

## Documentation

- [Architecture](docs/architecture.md): current package boundaries and data flow.
- [Methodology](docs/methodology.md): pricing equations, assumptions, and limits.
- [Data dictionary](docs/data_dictionary.md): input fields and output records.
- [Roadmap](docs/roadmap.md): differentiated product direction and delivery gates.

## Development checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv build
```

`pytest` enforces at least 80% coverage of the installable `at1radar` package.
The Streamlit app sits outside that coverage target, so UI changes also need a
Streamlit `AppTest` smoke check.
