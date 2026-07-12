"""Tests for coupon schedule generation with fixed, deterministic dates."""

from __future__ import annotations

from datetime import date

import pytest

from at1radar.cashflows.schedule import (
    ScheduleError,
    add_months,
    generate_coupon_schedule,
    year_fraction,
)
from at1radar.domain.instruments import AT1Instrument, DayCount
from tests.conftest import VALUATION_DATE

RESET_BENCHMARK_RATE = 0.03


def test_no_cashflow_on_or_before_valuation_date(alpha_instrument: AT1Instrument) -> None:
    # 2025-09-15 coupon exists; valuation on that date must exclude it.
    schedule = generate_coupon_schedule(
        alpha_instrument, date(2025, 9, 15), alpha_instrument.first_call_date, RESET_BENCHMARK_RATE
    )
    assert (schedule["payment_date"] > date(2025, 9, 15)).all()
    assert schedule["payment_date"].min() == date(2026, 3, 15)


def test_final_payment_contains_principal(alpha_instrument: AT1Instrument) -> None:
    schedule = generate_coupon_schedule(
        alpha_instrument, VALUATION_DATE, alpha_instrument.first_call_date, RESET_BENCHMARK_RATE
    )
    final = schedule.iloc[-1]
    assert final["payment_date"] == alpha_instrument.first_call_date
    assert final["principal_cashflow"] == alpha_instrument.notional
    assert final["total_cashflow"] == pytest.approx(
        final["coupon_cashflow"] + alpha_instrument.notional
    )
    # Only the terminal row carries principal.
    assert (schedule["principal_cashflow"].iloc[:-1] == 0.0).all()


def test_pre_reset_coupons_use_fixed_rate(alpha_instrument: AT1Instrument) -> None:
    schedule = generate_coupon_schedule(
        alpha_instrument, VALUATION_DATE, alpha_instrument.first_call_date, RESET_BENCHMARK_RATE
    )
    assert not schedule["is_post_reset"].any()
    assert (schedule["coupon_rate"] == alpha_instrument.current_coupon_rate).all()


def test_post_reset_coupons_use_benchmark_plus_margin(alpha_instrument: AT1Instrument) -> None:
    extended_terminal = add_months(
        alpha_instrument.first_call_date, alpha_instrument.subsequent_call_frequency_months
    )
    schedule = generate_coupon_schedule(
        alpha_instrument, VALUATION_DATE, extended_terminal, RESET_BENCHMARK_RATE
    )
    post_reset = schedule[schedule["is_post_reset"]]
    pre_reset = schedule[~schedule["is_post_reset"]]
    expected_reset_rate = RESET_BENCHMARK_RATE + alpha_instrument.reset_margin_bps / 10_000
    assert not post_reset.empty
    assert post_reset["coupon_rate"].unique().tolist() == pytest.approx([expected_reset_rate])
    assert (pre_reset["coupon_rate"] == alpha_instrument.current_coupon_rate).all()
    # Reset applies to periods starting on/after the first call date.
    assert post_reset["period_start"].min() == alpha_instrument.first_call_date


def test_semiannual_payment_count(alpha_instrument: AT1Instrument) -> None:
    # Valuation 2025-06-30, first call 2027-03-15: 2025-09-15 ... 2027-03-15.
    called = generate_coupon_schedule(
        alpha_instrument, VALUATION_DATE, alpha_instrument.first_call_date, RESET_BENCHMARK_RATE
    )
    assert len(called) == 4
    # Extended by 60 months to 2032-03-15 adds 10 semiannual payments.
    extended = generate_coupon_schedule(
        alpha_instrument, VALUATION_DATE, date(2032, 3, 15), RESET_BENCHMARK_RATE
    )
    assert len(extended) == 14


def test_quarterly_payment_count(beta_instrument: AT1Instrument) -> None:
    # Valuation 2025-06-30, first call 2028-06-30: 12 quarterly payments.
    called = generate_coupon_schedule(
        beta_instrument, VALUATION_DATE, beta_instrument.first_call_date, RESET_BENCHMARK_RATE
    )
    assert len(called) == 12
    extended = generate_coupon_schedule(
        beta_instrument, VALUATION_DATE, date(2029, 6, 30), RESET_BENCHMARK_RATE
    )
    assert len(extended) == 16


def test_misaligned_terminal_date_rejected(alpha_instrument: AT1Instrument) -> None:
    with pytest.raises(ScheduleError, match="does not fall on"):
        generate_coupon_schedule(
            alpha_instrument, VALUATION_DATE, date(2027, 4, 1), RESET_BENCHMARK_RATE
        )


def test_terminal_before_valuation_rejected(alpha_instrument: AT1Instrument) -> None:
    with pytest.raises(ScheduleError, match="must be after"):
        generate_coupon_schedule(
            alpha_instrument,
            date(2028, 1, 1),
            alpha_instrument.first_call_date,
            RESET_BENCHMARK_RATE,
        )


def test_terminal_before_first_call_rejected(alpha_instrument: AT1Instrument) -> None:
    with pytest.raises(ScheduleError, match="before the first call date"):
        generate_coupon_schedule(
            alpha_instrument, date(2024, 1, 1), date(2025, 3, 15), RESET_BENCHMARK_RATE
        )


def test_coupon_amount_uses_year_fraction(beta_instrument: AT1Instrument) -> None:
    schedule = generate_coupon_schedule(
        beta_instrument, VALUATION_DATE, beta_instrument.first_call_date, RESET_BENCHMARK_RATE
    )
    first = schedule.iloc[0]
    # ACT_365: 2025-06-30 -> 2025-09-30 is 92 days.
    assert first["year_fraction"] == pytest.approx(92 / 365)
    assert first["coupon_cashflow"] == pytest.approx(
        beta_instrument.notional * beta_instrument.current_coupon_rate * 92 / 365
    )


def test_add_months_clamps_month_end() -> None:
    assert add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert add_months(date(2021, 6, 30), 3) == date(2021, 9, 30)
    assert add_months(date(2025, 12, 15), 3) == date(2026, 3, 15)


def test_year_fraction_conventions() -> None:
    assert year_fraction(date(2025, 1, 1), date(2025, 7, 1), DayCount.ACT_365) == pytest.approx(
        181 / 365
    )
    assert year_fraction(date(2025, 1, 1), date(2025, 7, 1), DayCount.ACT_ACT) == pytest.approx(
        181 / 365.25
    )
    assert year_fraction(
        date(2025, 1, 30), date(2025, 7, 30), DayCount.THIRTY_360
    ) == pytest.approx(0.5)
    assert year_fraction(
        date(2025, 1, 31), date(2025, 7, 31), DayCount.THIRTY_360
    ) == pytest.approx(0.5)
    assert year_fraction(
        date(2025, 2, 28), date(2025, 8, 31), DayCount.THIRTY_360
    ) == pytest.approx(0.5)
    assert year_fraction(
        date(2024, 2, 29), date(2024, 8, 31), DayCount.THIRTY_360
    ) == pytest.approx(0.5)
    assert year_fraction(
        date(2024, 2, 29), date(2025, 2, 28), DayCount.THIRTY_360
    ) == pytest.approx(1.0)


def test_year_fraction_rejects_reversed_dates() -> None:
    with pytest.raises(ValueError, match="before start"):
        year_fraction(date(2025, 7, 1), date(2025, 1, 1), DayCount.ACT_365)


@pytest.mark.parametrize("reset_rate", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_reset_rate_rejected(alpha_instrument: AT1Instrument, reset_rate: float) -> None:
    with pytest.raises(ScheduleError, match="must be finite"):
        generate_coupon_schedule(
            alpha_instrument,
            VALUATION_DATE,
            alpha_instrument.first_call_date,
            reset_rate,
        )
