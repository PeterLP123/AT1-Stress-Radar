"""Typed domain model for AT1 instruments.

Conventions
-----------
- All rates are stored as decimals: ``0.065`` means 6.5% per annum.
- The one exception is ``reset_margin_bps``, which is stored in basis points
  as quoted in term sheets and converted with ``bps / 10_000`` (see the
  :attr:`AT1Instrument.reset_margin` property).
- The CET1 trigger is a decimal ratio: ``0.05125`` means 5.125%.

This model intentionally covers only the contractual features needed for the
current called/extended state valuation. It does not attempt to represent the
full legal complexity of an AT1 prospectus.
"""

from __future__ import annotations

import calendar
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Currency(StrEnum):
    """Supported instrument currencies. EUR only in the initial scope."""

    EUR = "EUR"


class CouponFrequency(StrEnum):
    """Supported coupon payment frequencies."""

    ANNUAL = "annual"
    SEMIANNUAL = "semiannual"
    QUARTERLY = "quarterly"

    @property
    def months_per_period(self) -> int:
        """Number of calendar months in one coupon period."""
        return _MONTHS_PER_PERIOD[self]

    @property
    def periods_per_year(self) -> int:
        """Number of coupon periods per year."""
        return 12 // self.months_per_period


_MONTHS_PER_PERIOD: dict[CouponFrequency, int] = {
    CouponFrequency.ANNUAL: 12,
    CouponFrequency.SEMIANNUAL: 6,
    CouponFrequency.QUARTERLY: 3,
}


class DayCount(StrEnum):
    """Supported day-count conventions (simplified implementations)."""

    ACT_ACT = "ACT_ACT"
    ACT_365 = "ACT_365"
    THIRTY_360 = "THIRTY_360"


class LossAbsorptionType(StrEnum):
    """Contractual loss-absorption mechanism at the CET1 trigger."""

    TEMPORARY_WRITE_DOWN = "temporary_write_down"
    PERMANENT_WRITE_DOWN = "permanent_write_down"
    EQUITY_CONVERSION = "equity_conversion"


class AT1Instrument(BaseModel):
    """Contractual terms of a single fixed-to-reset perpetual AT1 instrument.

    All fields are required unless explicitly optional; missing required
    fields are a validation error, never silently defaulted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    instrument_id: str = Field(min_length=1, description="Internal stable identifier.")
    isin: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$",
        description="Optional ISIN; synthetic instruments usually have none.",
    )
    issuer_id: str = Field(min_length=1)
    issuer_name: str = Field(min_length=1)
    instrument_name: str = Field(min_length=1)
    currency: Currency
    issue_date: date
    notional: float = Field(gt=0, description="Face amount in instrument currency.")
    current_coupon_rate: float = Field(
        ge=0, le=0.5, description="Fixed coupon before first reset, as a decimal."
    )
    coupon_frequency: CouponFrequency
    day_count: DayCount
    first_call_date: date
    subsequent_call_frequency_months: int = Field(
        gt=0, le=120, description="Months between call dates after the first call date."
    )
    reset_benchmark: str = Field(
        min_length=1, description="Name of the reset benchmark, e.g. EUR_MID_SWAP_5Y."
    )
    reset_margin_bps: float = Field(
        ge=0, le=2_000, description="Contractual reset margin in basis points."
    )
    contractual_cet1_trigger: float = Field(
        gt=0, lt=1, description="CET1 trigger ratio as a decimal, e.g. 0.05125."
    )
    loss_absorption_type: LossAbsorptionType
    coupon_discretion: bool = Field(
        description="Whether coupons are fully discretionary (true for real AT1s)."
    )
    governing_law: str = Field(min_length=1)
    terms_source: str = Field(min_length=1, description="Where the terms were taken from.")
    terms_verified_date: date
    is_synthetic: bool = Field(
        description="Must be explicitly true for synthetic (fictional) instruments."
    )

    @model_validator(mode="after")
    def _validate_dates(self) -> AT1Instrument:
        if self.first_call_date <= self.issue_date:
            raise ValueError(
                f"first_call_date ({self.first_call_date}) must be after "
                f"issue_date ({self.issue_date})"
            )
        months_to_first_call = (self.first_call_date.year - self.issue_date.year) * 12 + (
            self.first_call_date.month - self.issue_date.month
        )
        coupon_months = self.coupon_frequency.months_per_period
        expected_call_day = min(
            self.issue_date.day,
            calendar.monthrange(self.first_call_date.year, self.first_call_date.month)[1],
        )
        if (
            months_to_first_call % coupon_months != 0
            or self.first_call_date.day != expected_call_day
        ):
            raise ValueError(
                f"first_call_date ({self.first_call_date}) must fall on the "
                f"{self.coupon_frequency.value} coupon schedule anchored at "
                f"issue_date ({self.issue_date})"
            )
        if self.subsequent_call_frequency_months % coupon_months != 0:
            raise ValueError(
                "subsequent_call_frequency_months "
                f"({self.subsequent_call_frequency_months}) must be a multiple of the "
                f"{coupon_months}-month coupon period"
            )
        return self

    @property
    def reset_margin(self) -> float:
        """Reset margin as a decimal, converted with ``bps / 10_000``."""
        return self.reset_margin_bps / 10_000
