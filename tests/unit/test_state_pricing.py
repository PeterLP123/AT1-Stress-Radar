"""Tests for the simplified state-pricing model."""

from __future__ import annotations

from datetime import date

import pytest

from at1radar.cashflows.schedule import add_months, generate_coupon_schedule
from at1radar.domain.instruments import AT1Instrument
from at1radar.domain.scenarios import CallState
from at1radar.pricing.state_pricing import (
    DAYS_PER_YEAR,
    terminal_date_for_state,
    value_both_states,
    value_state,
)
from tests.conftest import VALUATION_DATE, make_instrument

DISCOUNT_RATE = 0.08
RESET_BENCHMARK_RATE = 0.03


def test_higher_discount_rate_lowers_present_value(alpha_instrument: AT1Instrument) -> None:
    for state in CallState:
        low = value_state(alpha_instrument, state, VALUATION_DATE, 0.05, RESET_BENCHMARK_RATE)
        high = value_state(alpha_instrument, state, VALUATION_DATE, 0.10, RESET_BENCHMARK_RATE)
        assert high.present_value < low.present_value


def test_called_state_terminates_at_first_call(alpha_instrument: AT1Instrument) -> None:
    result = value_state(
        alpha_instrument,
        CallState.CALLED_AT_FIRST_CALL,
        VALUATION_DATE,
        DISCOUNT_RATE,
        RESET_BENCHMARK_RATE,
    )
    assert result.terminal_date == alpha_instrument.first_call_date
    assert result.cashflows["payment_date"].max() == alpha_instrument.first_call_date
    assert not result.cashflows["is_post_reset"].any()


def test_extended_state_terminates_at_next_call(alpha_instrument: AT1Instrument) -> None:
    result = value_state(
        alpha_instrument,
        CallState.EXTENDED_TO_NEXT_CALL,
        VALUATION_DATE,
        DISCOUNT_RATE,
        RESET_BENCHMARK_RATE,
    )
    expected_terminal = add_months(
        alpha_instrument.first_call_date, alpha_instrument.subsequent_call_frequency_months
    )
    assert result.terminal_date == expected_terminal == date(2032, 3, 15)
    assert result.cashflows["payment_date"].max() == expected_terminal
    # The extension changes the schedule: more cash flows, including post-reset ones.
    assert result.cashflows["is_post_reset"].any()


def test_month_end_extension_preserves_issue_date_schedule_anchor() -> None:
    instrument = make_instrument(
        issue_date=date(2024, 8, 31),
        first_call_date=date(2025, 2, 28),
        subsequent_call_frequency_months=6,
    )
    result = value_state(
        instrument,
        CallState.EXTENDED_TO_NEXT_CALL,
        date(2024, 8, 31),
        DISCOUNT_RATE,
        RESET_BENCHMARK_RATE,
    )
    assert result.terminal_date == date(2025, 8, 31)
    assert result.cashflows["payment_date"].max() == date(2025, 8, 31)


def test_extension_changes_cashflow_schedule(beta_instrument: AT1Instrument) -> None:
    results = value_both_states(
        beta_instrument, VALUATION_DATE, DISCOUNT_RATE, RESET_BENCHMARK_RATE
    )
    called = results[CallState.CALLED_AT_FIRST_CALL]
    extended = results[CallState.EXTENDED_TO_NEXT_CALL]
    assert extended.num_cashflows > called.num_cashflows
    assert extended.terminal_date == date(2029, 6, 30)
    assert called.terminal_date == date(2028, 6, 30)


def test_price_is_normalised_to_notional(alpha_instrument: AT1Instrument) -> None:
    result = value_state(
        alpha_instrument,
        CallState.CALLED_AT_FIRST_CALL,
        VALUATION_DATE,
        DISCOUNT_RATE,
        RESET_BENCHMARK_RATE,
    )
    assert result.model_price_pct_of_notional == pytest.approx(
        100.0 * result.present_value / alpha_instrument.notional
    )


def test_present_value_reconciles_with_manual_discounting(
    beta_instrument: AT1Instrument,
) -> None:
    state = CallState.EXTENDED_TO_NEXT_CALL
    result = value_state(
        beta_instrument, state, VALUATION_DATE, DISCOUNT_RATE, RESET_BENCHMARK_RATE
    )
    schedule = generate_coupon_schedule(
        beta_instrument,
        VALUATION_DATE,
        terminal_date_for_state(beta_instrument, state),
        RESET_BENCHMARK_RATE,
    )
    payment_dates: list[date] = schedule["payment_date"].tolist()
    total_cashflows: list[float] = schedule["total_cashflow"].tolist()
    manual_pv = sum(
        cashflow * (1.0 + DISCOUNT_RATE) ** -((payment - VALUATION_DATE).days / DAYS_PER_YEAR)
        for payment, cashflow in zip(payment_dates, total_cashflows, strict=True)
    )
    assert result.present_value == pytest.approx(manual_pv)
    assert result.num_cashflows == len(schedule)


def test_num_cashflows_matches_schedule(alpha_instrument: AT1Instrument) -> None:
    result = value_state(
        alpha_instrument,
        CallState.CALLED_AT_FIRST_CALL,
        VALUATION_DATE,
        DISCOUNT_RATE,
        RESET_BENCHMARK_RATE,
    )
    assert result.num_cashflows == 4 == len(result.cashflows)


def test_assumptions_recorded(alpha_instrument: AT1Instrument) -> None:
    result = value_state(
        alpha_instrument,
        CallState.CALLED_AT_FIRST_CALL,
        VALUATION_DATE,
        DISCOUNT_RATE,
        RESET_BENCHMARK_RATE,
    )
    assert result.assumptions["valuation_date"] == VALUATION_DATE.isoformat()
    assert result.assumptions["flat_discount_rate"] == DISCOUNT_RATE
    assert result.assumptions["assumed_reset_benchmark_rate"] == RESET_BENCHMARK_RATE


def test_valuation_on_or_after_first_call_rejected(alpha_instrument: AT1Instrument) -> None:
    with pytest.raises(ValueError, match="before the first call date"):
        value_state(
            alpha_instrument,
            CallState.EXTENDED_TO_NEXT_CALL,
            alpha_instrument.first_call_date,
            DISCOUNT_RATE,
            RESET_BENCHMARK_RATE,
        )


def test_valuation_before_issue_rejected(alpha_instrument: AT1Instrument) -> None:
    with pytest.raises(ValueError, match="on or after the issue date"):
        value_state(
            alpha_instrument,
            CallState.CALLED_AT_FIRST_CALL,
            date(2022, 3, 14),
            DISCOUNT_RATE,
            RESET_BENCHMARK_RATE,
        )


def test_valuation_on_issue_date_allowed(alpha_instrument: AT1Instrument) -> None:
    result = value_state(
        alpha_instrument,
        CallState.CALLED_AT_FIRST_CALL,
        alpha_instrument.issue_date,
        DISCOUNT_RATE,
        RESET_BENCHMARK_RATE,
    )
    assert result.present_value > 0


def test_discount_rate_below_minus_one_rejected(alpha_instrument: AT1Instrument) -> None:
    with pytest.raises(ValueError, match="greater than -1"):
        value_state(
            alpha_instrument,
            CallState.CALLED_AT_FIRST_CALL,
            VALUATION_DATE,
            -1.5,
            RESET_BENCHMARK_RATE,
        )


@pytest.mark.parametrize("discount_rate", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_discount_rate_rejected(
    alpha_instrument: AT1Instrument, discount_rate: float
) -> None:
    with pytest.raises(ValueError, match="flat_discount_rate must be finite"):
        value_state(
            alpha_instrument,
            CallState.CALLED_AT_FIRST_CALL,
            VALUATION_DATE,
            discount_rate,
            RESET_BENCHMARK_RATE,
        )


@pytest.mark.parametrize("reset_rate", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_reset_rate_rejected(alpha_instrument: AT1Instrument, reset_rate: float) -> None:
    with pytest.raises(ValueError, match="assumed_reset_benchmark_rate must be finite"):
        value_state(
            alpha_instrument,
            CallState.EXTENDED_TO_NEXT_CALL,
            VALUATION_DATE,
            DISCOUNT_RATE,
            reset_rate,
        )
