"""Validation tests for the AT1 instrument domain model."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from at1radar.domain.instruments import AT1Instrument, CouponFrequency
from tests.conftest import ALPHA_TERMS, make_instrument


def test_valid_instrument_loads() -> None:
    instrument = make_instrument()
    assert instrument.instrument_id == "synthetic-alpha"
    assert instrument.currency == "EUR"
    assert instrument.coupon_frequency is CouponFrequency.SEMIANNUAL


def test_negative_notional_rejected() -> None:
    with pytest.raises(ValidationError, match="notional"):
        make_instrument(notional=-100.0)


def test_zero_notional_rejected() -> None:
    with pytest.raises(ValidationError, match="notional"):
        make_instrument(notional=0.0)


@pytest.mark.parametrize("notional", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_notional_rejected(notional: float) -> None:
    with pytest.raises(ValidationError, match="notional"):
        make_instrument(notional=notional)


def test_negative_coupon_rejected() -> None:
    with pytest.raises(ValidationError, match="current_coupon_rate"):
        make_instrument(current_coupon_rate=-0.01)


def test_first_call_before_issue_rejected() -> None:
    with pytest.raises(ValidationError, match="first_call_date"):
        make_instrument(first_call_date=date(2021, 3, 15))


def test_first_call_equal_to_issue_rejected() -> None:
    with pytest.raises(ValidationError, match="first_call_date"):
        make_instrument(first_call_date=ALPHA_TERMS["issue_date"])


def test_first_call_off_coupon_schedule_rejected() -> None:
    with pytest.raises(ValidationError, match="must fall on the semiannual coupon schedule"):
        make_instrument(first_call_date=date(2027, 4, 15))


def test_subsequent_call_frequency_off_coupon_schedule_rejected() -> None:
    with pytest.raises(ValidationError, match="must be a multiple"):
        make_instrument(subsequent_call_frequency_months=1)


def test_month_end_first_call_on_coupon_schedule_accepted() -> None:
    instrument = make_instrument(
        issue_date=date(2024, 8, 31),
        first_call_date=date(2025, 2, 28),
        subsequent_call_frequency_months=6,
    )
    assert instrument.first_call_date == date(2025, 2, 28)


def test_invalid_loss_absorption_type_rejected() -> None:
    with pytest.raises(ValidationError, match="loss_absorption_type"):
        make_instrument(loss_absorption_type="contingent_haircut")


@pytest.mark.parametrize("trigger", [0.0, -0.05, 1.0, 1.2])
def test_cet1_trigger_outside_range_rejected(trigger: float) -> None:
    with pytest.raises(ValidationError, match="contractual_cet1_trigger"):
        make_instrument(contractual_cet1_trigger=trigger)


@pytest.mark.parametrize("margin", [-10.0, 5_000.0])
def test_unreasonable_reset_margin_rejected(margin: float) -> None:
    with pytest.raises(ValidationError, match="reset_margin_bps"):
        make_instrument(reset_margin_bps=margin)


def test_missing_is_synthetic_rejected() -> None:
    terms = {k: v for k, v in ALPHA_TERMS.items() if k != "is_synthetic"}
    with pytest.raises(ValidationError, match="is_synthetic"):
        AT1Instrument.model_validate(terms)


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError, match="mystery_field"):
        make_instrument(mystery_field=1)


def test_invalid_isin_rejected() -> None:
    with pytest.raises(ValidationError, match="isin"):
        make_instrument(isin="not-an-isin")


def test_reset_margin_converted_with_bps_over_10_000() -> None:
    instrument = make_instrument(reset_margin_bps=450.0)
    assert instrument.reset_margin == pytest.approx(0.045)
