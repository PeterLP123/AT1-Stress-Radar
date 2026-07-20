"""Simplified deterministic state valuation for AT1 instruments.

Two transparent states are supported:

- ``called_at_first_call``: the instrument is redeemed at par on the first
  call date.
- ``extended_to_next_call``: the call is skipped once; the instrument is
  redeemed at par on the first call date plus the instrument's subsequent
  call frequency.

Each state is valued by discounting the contractual cash flows with a single
flat annual rate. Discount factors are ``(1 + r) ** -t`` where ``t`` is
actual days from the valuation date to payment divided by 365.25.

The result is deliberately called a *model value* (or simplified state
value), not a fair value: there is no curve, no credit model, no call
probability weighting, and no coupon-cancellation risk. See
``docs/methodology.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite

import pandas as pd

from at1radar.cashflows.schedule import generate_coupon_schedule
from at1radar.dates import add_months, months_between
from at1radar.domain.instruments import AT1Instrument
from at1radar.domain.scenarios import CallState

DAYS_PER_YEAR = 365.25
"""Days-per-year convention used to convert calendar days to discounting time."""


@dataclass(frozen=True)
class StateValuationResult:
    """Outcome of valuing one instrument under one deterministic call state.

    ``present_value`` is in instrument currency;
    ``model_price_pct_of_notional`` is the same value expressed as a
    percentage of notional (100.0 == par).
    """

    state: CallState
    terminal_date: date
    present_value: float
    model_price_pct_of_notional: float
    num_cashflows: int
    assumptions: dict[str, str | float]
    cashflows: pd.DataFrame


def terminal_date_for_state(instrument: AT1Instrument, state: CallState) -> date:
    """Redemption date implied by a deterministic call state.

    Extension is anchored at the issue date (not the first call date) so that
    month-end instruments stay on the coupon schedule after a skipped call.
    """
    if state is CallState.CALLED_AT_FIRST_CALL:
        return instrument.first_call_date
    return add_months(
        instrument.issue_date,
        months_between(instrument.issue_date, instrument.first_call_date)
        + instrument.subsequent_call_frequency_months,
    )


def value_state(
    instrument: AT1Instrument,
    state: CallState,
    valuation_date: date,
    flat_discount_rate: float,
    assumed_reset_benchmark_rate: float,
) -> StateValuationResult:
    """Value an instrument under one deterministic call state.

    Parameters
    ----------
    instrument:
        The AT1 instrument to value.
    state:
        Which deterministic call state to assume.
    valuation_date:
        Must be on or after issue and before the first call date. Pricing
        outside that interval is out of scope for this prototype.
    flat_discount_rate:
        Single flat annual discount rate as a decimal (e.g. ``0.08``).
    assumed_reset_benchmark_rate:
        Decimal benchmark rate assumed constant after the first reset.
    """
    if not isfinite(flat_discount_rate):
        raise ValueError(f"flat_discount_rate must be finite, got {flat_discount_rate}")
    if not isfinite(assumed_reset_benchmark_rate):
        raise ValueError(
            f"assumed_reset_benchmark_rate must be finite, got {assumed_reset_benchmark_rate}"
        )
    if flat_discount_rate <= -1.0:
        raise ValueError(f"flat_discount_rate must be greater than -1, got {flat_discount_rate}")
    if valuation_date < instrument.issue_date:
        raise ValueError(
            f"valuation_date ({valuation_date}) must be on or after the issue date "
            f"({instrument.issue_date})"
        )
    if valuation_date >= instrument.first_call_date:
        raise ValueError(
            f"valuation_date ({valuation_date}) must be before the first call date "
            f"({instrument.first_call_date}); later valuation dates are out of scope"
        )

    terminal_date = terminal_date_for_state(instrument, state)
    cashflows = generate_coupon_schedule(
        instrument=instrument,
        valuation_date=valuation_date,
        terminal_call_date=terminal_date,
        assumed_reset_benchmark_rate=assumed_reset_benchmark_rate,
    )

    days = pd.to_datetime(cashflows["payment_date"]) - pd.Timestamp(valuation_date)
    years_to_payment = days.dt.days / DAYS_PER_YEAR
    discount_factors = (1.0 + flat_discount_rate) ** -years_to_payment
    cashflows = cashflows.assign(
        years_to_payment=years_to_payment,
        discount_factor=discount_factors,
        present_value=cashflows["total_cashflow"] * discount_factors,
    )
    present_value = float(cashflows["present_value"].sum(skipna=False))
    if not isfinite(present_value):
        raise ValueError("valuation produced a non-finite present value; check the inputs")

    return StateValuationResult(
        state=state,
        terminal_date=terminal_date,
        present_value=present_value,
        model_price_pct_of_notional=100.0 * present_value / instrument.notional,
        num_cashflows=len(cashflows),
        assumptions={
            "valuation_date": valuation_date.isoformat(),
            "flat_discount_rate": flat_discount_rate,
            "assumed_reset_benchmark_rate": assumed_reset_benchmark_rate,
            "reset_margin_bps": instrument.reset_margin_bps,
            "discounting": f"(1 + r)^-t with t = actual days / {DAYS_PER_YEAR}",
        },
        cashflows=cashflows,
    )


def value_both_states(
    instrument: AT1Instrument,
    valuation_date: date,
    flat_discount_rate: float,
    assumed_reset_benchmark_rate: float,
) -> dict[CallState, StateValuationResult]:
    """Value an instrument under both deterministic call states."""
    return {
        state: value_state(
            instrument=instrument,
            state=state,
            valuation_date=valuation_date,
            flat_discount_rate=flat_discount_rate,
            assumed_reset_benchmark_rate=assumed_reset_benchmark_rate,
        )
        for state in CallState
    }
