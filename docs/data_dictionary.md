# Data dictionary

Conventions used throughout: **rates are decimals** (`0.065` = 6.5%);
**dates** are ISO `YYYY-MM-DD` (PyYAML parses them to `datetime.date`). The
implemented cash-flow engine converts `reset_margin_bps` with `bps / 10_000`.
Scenario `*_shock_bps` fields are expressed in basis points but are only
validated in version `0.1.0`; no scenario shock is converted or applied yet.

## Instrument fields (`data/instruments/*.yaml`)

One YAML mapping per file, validated by `at1radar.domain.instruments.AT1Instrument`.
All fields are required unless marked optional; missing required fields fail
validation rather than being defaulted.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `instrument_id` | str | non-empty, unique across the universe | Internal stable identifier used by the CLI and app. |
| `isin` | str or null | optional; `^[A-Z]{2}[A-Z0-9]{9}[0-9]$` | ISIN if one exists; `null` for synthetic instruments. |
| `issuer_id` | str | non-empty | Internal issuer identifier. |
| `issuer_name` | str | non-empty | Display name of the issuer. |
| `instrument_name` | str | non-empty | Display name of the instrument. |
| `currency` | enum | `EUR` only (initial scope) | Instrument currency. |
| `issue_date` | date | — | Issue/settlement date anchoring the coupon schedule. |
| `notional` | float | > 0 | Face amount in instrument currency. |
| `current_coupon_rate` | float | 0 ≤ x ≤ 0.5 | Fixed annual coupon before the first reset, as a decimal. |
| `coupon_frequency` | enum | `annual`, `semiannual`, `quarterly` | Coupon payment frequency. |
| `day_count` | enum | `ACT_ACT`, `ACT_365`, `THIRTY_360` | Day-count convention for coupon accrual (simplified; see methodology). |
| `first_call_date` | date | after `issue_date`; on issue-anchored coupon schedule | First issuer call date; also the coupon reset date. |
| `subsequent_call_frequency_months` | int | 1–120; multiple of coupon period | Months between call dates after the first call date. |
| `reset_benchmark` | str | non-empty | Name of the reset benchmark, e.g. `EUR_MID_SWAP_5Y`. Descriptive only for now. |
| `reset_margin_bps` | float | 0–2000 | Contractual reset margin in **basis points**; converted as `bps / 10_000`. |
| `contractual_cet1_trigger` | float | 0 < x < 1 | CET1 trigger ratio as a decimal (`0.05125` = 5.125%). Recorded, not yet modelled. |
| `loss_absorption_type` | enum | `temporary_write_down`, `permanent_write_down`, `equity_conversion` | Loss-absorption mechanism at the trigger. Recorded, not yet modelled. |
| `coupon_discretion` | bool | — | Whether coupons are fully discretionary (true for real AT1s). Recorded, not yet modelled. |
| `governing_law` | str | non-empty | Governing law of the terms. |
| `terms_source` | str | non-empty | Provenance of the terms data. |
| `terms_verified_date` | date | — | When the terms were last checked against the source. |
| `is_synthetic` | bool | must be explicitly present | `true` for fictional instruments. Synthetic files must set this explicitly. |

## Scenario fields (`data/scenarios/*.yaml`)

A file holds a top-level `scenarios:` list, each entry validated by
`at1radar.domain.scenarios.Scenario`. **These fields are placeholders for a
future decomposition engine** — the current application validates them but
does not apply the shocks.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `name` | str | non-empty, unique in file | Scenario identifier. |
| `description` | str | non-empty | Human-readable description. |
| `risk_free_rate_shock_bps` | float | −1000 to 1000 | Parallel shock to the risk-free rate, in basis points. |
| `credit_spread_shock_bps` | float | −2000 to 2000 | Shock to the instrument's credit spread, in basis points. |
| `reset_rate_shock_bps` | float | −1000 to 1000 | Shock to the assumed reset benchmark rate, in basis points. |
| `call_assumption` | enum | `called_at_first_call`, `extended_to_next_call` | Deterministic call state; may become a call probability later. |
| `issuer_equity_shock` | float or null | optional; −1 to 1 | Issuer equity return shock as a decimal (`-0.30` = −30%). |
| `cet1_ratio_shock` | float or null | optional; −0.2 to 0.2 | Additive shock to the CET1 ratio as a decimal (`-0.02` = −2 percentage points). |

## State valuation result

`at1radar.pricing.state_pricing.value_state` returns a frozen
`StateValuationResult`. `value_both_states` returns one result per `CallState`.

| Field | Type | Description |
|---|---|---|
| `state` | `CallState` | Deterministic call assumption used for the valuation. |
| `terminal_date` | date | Assumed par-redemption date for the state. |
| `present_value` | float | Sum of discounted cash flows in instrument currency. |
| `model_price_pct_of_notional` | float | `100 * present_value / notional`; `100.0` means par. |
| `num_cashflows` | int | Number of future payment rows included. |
| `assumptions` | dict | Valuation date, flat discount rate, assumed reset benchmark, reset margin, and discounting convention used. |
| `cashflows` | pandas DataFrame | Contractual schedule plus discounting columns described below. |

## Cash-flow schedule columns

Output of `at1radar.cashflows.schedule.generate_coupon_schedule` (one row per
remaining payment):

| Column | Type | Description |
|---|---|---|
| `payment_date` | date | Date the cash flow is paid (equals `period_end`; no business-day adjustment). |
| `period_start` | date | Accrual period start. |
| `period_end` | date | Accrual period end. |
| `year_fraction` | float | Accrual fraction under the instrument's day-count convention. |
| `coupon_rate` | float | Annual rate applied to the period (fixed pre-reset; benchmark + margin post-reset). |
| `coupon_cashflow` | float | `notional * coupon_rate * year_fraction`. |
| `principal_cashflow` | float | `notional` on the terminal call date, else 0. |
| `total_cashflow` | float | Coupon plus principal. |
| `is_post_reset` | bool | True if the period starts on or after the first call date. |

`at1radar.pricing.state_pricing.value_state` appends `years_to_payment`
(actual days / 365.25), `discount_factor`, and `present_value` columns to the
schedule it returns in `StateValuationResult.cashflows`.

## Related documentation

- [README](../README.md)
- [Architecture](architecture.md)
- [Methodology](methodology.md)
- [Roadmap](roadmap.md)
