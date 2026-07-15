# Architecture

AT1 Stress Radar is a small `src`-layout Python package with thin CLI and
Streamlit entry points. Domain rules and calculations stay independent of the
presentation layer so the same result can be reproduced in tests, scripts, or
the app.

## Current data flow

```text
instrument YAML --> defensive loader --> AT1Instrument
                                             |
call state + valuation assumptions ---------+
                                             v
                                      state pricing
                                             |
                                             v
                                      coupon schedule
                                             |
                                             v
                                  StateValuationResult --> CLI / Streamlit

scenario YAML --> defensive loader --> Scenario --> validation output
                                               (no pricing edge today)
```

The scenario branch stops after validation in version `0.1.0`. No scenario
shock reaches pricing yet.

## Package dependencies

Arrows point from a consumer to the package it depends on:

```text
data ------------------------> domain
cashflows -------------------> domain
pricing ---------------------> domain, cashflows
cli -------------------------> domain, data, pricing
app/streamlit_app.py --------> domain, data, pricing
```

Dependencies remain one-way. In particular, domain models never import file
loaders, pricing code, or the user interfaces.

### `at1radar.domain`

Frozen Pydantic models and controlled vocabularies only.

- `instruments.py` defines `AT1Instrument`, currency, coupon frequency,
  day-count, and loss-absorption types.
- `scenarios.py` defines the starting `Scenario` input contract and
  `CallState`. `CallState` lives here because cash-flow valuation and future
  scenario logic both need it.

This layer validates structural and contractual invariants, including finite
numbers, call dates aligned to the issue-anchored coupon schedule, and
subsequent call frequencies compatible with coupon periods.

### `at1radar.data`

YAML ingestion and validation. The loaders turn missing files, unreadable
content, malformed YAML, duplicate identifiers, and schema failures into
path-aware `InstrumentLoadError` or `ScenarioLoadError` messages. They never
silently fill missing required fields.

### `at1radar.cashflows`

Pure schedule generation. An instrument, valuation date, terminal call date,
and assumed reset benchmark produce a pandas DataFrame of contractual cash
flows. The module owns calendar-month stepping and the simplified accrual
conventions.

### `at1radar.pricing`

Deterministic state valuation. It maps a `CallState` to a terminal date, asks
`cashflows` for the schedule, discounts each payment with one flat annual
rate, and returns a `StateValuationResult`. It has no file or UI concerns.

### CLI and Streamlit

`at1radar.cli` and `app/streamlit_app.py` are presentation adapters. They load
inputs, call package functions, handle domain-friendly errors, and format the
same underlying results. The Streamlit entry point remains outside the
installable package.

## Evolution rules

New roadmap work should preserve these boundaries:

1. Scenario application belongs in an engine above the domain models, not in
   `domain/scenarios.py`.
2. Market and regulatory data arrive through adapters that retain source,
   as-of date, retrieval time, units, and entity basis.
3. Cash-flow and loss-absorption mechanics remain deterministic before any
   probability or machine-learning layer is added.
4. CLI, UI, and future export/API surfaces consume shared result records rather
   than reimplementing calculations.
5. Licensed or user-supplied market observations stay separate from the
   synthetic, redistributable fixtures in this repository.

The [roadmap](roadmap.md) is the single source of truth for planned modules and
delivery order.

## Testing strategy

Unit tests in `tests/unit` use fixed dates and deterministic fixtures. They
cover domain validation, schedule boundary cases, day-count rules, pricing
reconciliation, loader failures, and CLI behavior. Repository YAML is used by
end-to-end CLI tests.

CI currently runs formatting, linting, mypy, and pytest with an 80% package
coverage floor. Two gaps remain explicit: the Streamlit `AppTest` smoke is not
yet committed to the suite, and the model has no independent external
valuation oracle. Both are hardening work in the roadmap.

## Related documentation

- [Methodology](methodology.md)
- [Data dictionary](data_dictionary.md)
- [Roadmap](roadmap.md)
