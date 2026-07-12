# Architecture

## Package boundaries

The project uses a `src` layout with one package, `at1radar`, split into
modules with strict one-way dependencies:

```
domain  <--  data (loaders)
domain  <--  cashflows
domain, cashflows  <--  pricing
domain, data, pricing  <--  cli
domain, data, pricing  <--  app/streamlit_app.py (outside the package)
```

### `at1radar.domain`

Pydantic models and enums only. No I/O, no pandas, no pricing logic.

- `instruments.py`: `AT1Instrument` and its controlled vocabularies
  (`Currency`, `CouponFrequency`, `DayCount`, `LossAbsorptionType`).
- `scenarios.py`: `Scenario` (a placeholder schema for the future
  decomposition engine) and `CallState`, the deterministic call states shared
  by scenarios and pricing. `CallState` lives in the domain layer so that
  pricing and scenarios can both reference it without a circular import.

### `at1radar.data`

YAML loading and validation. Translates file-level problems (missing files,
malformed YAML, schema violations) into `InstrumentLoadError` /
`ScenarioLoadError` with the offending path in the message. Never fills in
missing required fields with defaults.

### `at1radar.cashflows`

Pure schedule generation: instrument + valuation date + terminal call date +
assumed reset benchmark rate -> pandas DataFrame of contractual cash flows.
Contains the date arithmetic (`add_months`) and simplified day-count logic.

### `at1radar.pricing`

State-contingent valuation. Maps a `CallState` to a terminal date, asks
`cashflows` for the schedule, discounts at a flat rate, and returns a
`StateValuationResult`. No UI concerns, no file I/O.

### `at1radar.cli` and `app/streamlit_app.py`

Thin presentation layers. Both only wire user inputs to loaders and pricing
functions and format the results. The Streamlit app lives outside the
installable package because it is an entry point, not a library.

## Intended future modules

These are planned, not scaffolded (no empty abstractions yet):

- `at1radar.scenarios` (engine): apply `Scenario` shocks to valuation inputs
  and produce a value-change decomposition. The `Scenario` schema in
  `domain/scenarios.py` is the stable contract for this work.
- `at1radar.curves`: replace the flat discount rate with a simple curve /
  spread split (risk-free + credit spread), which the scenario shocks
  (`risk_free_rate_shock_bps`, `credit_spread_shock_bps`) are designed for.
- `at1radar.portfolio`: aggregate several instruments.

## Testing strategy

Unit tests live in `tests/unit` and use fixed deterministic dates
(`tests/conftest.py`). YAML fixtures for loader error paths live in
`tests/fixtures`. The CLI is tested end-to-end against the repository's
sample data; the Streamlit app is intentionally thin enough not to need
tests yet.
