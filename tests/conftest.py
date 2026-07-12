"""Shared fixtures with fixed, deterministic dates and assumptions."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from at1radar.domain.instruments import AT1Instrument

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# Fixed sample valuation date used across the tests: before both instruments'
# first call dates, after both issue dates.
VALUATION_DATE = date(2025, 6, 30)

ALPHA_TERMS: dict[str, Any] = {
    "instrument_id": "synthetic-alpha",
    "isin": None,
    "issuer_id": "SYNBANK-ALPHA",
    "issuer_name": "Synthetic Bank Alpha",
    "instrument_name": "Synthetic Bank Alpha 6.500% Perpetual AT1",
    "currency": "EUR",
    "issue_date": date(2022, 3, 15),
    "notional": 200_000.0,
    "current_coupon_rate": 0.065,
    "coupon_frequency": "semiannual",
    "day_count": "ACT_ACT",
    "first_call_date": date(2027, 3, 15),
    "subsequent_call_frequency_months": 60,
    "reset_benchmark": "EUR_MID_SWAP_5Y",
    "reset_margin_bps": 450.0,
    "contractual_cet1_trigger": 0.05125,
    "loss_absorption_type": "temporary_write_down",
    "coupon_discretion": True,
    "governing_law": "Synthetic (modelled on Irish law)",
    "terms_source": "synthetic fixture",
    "terms_verified_date": date(2026, 6, 30),
    "is_synthetic": True,
}

BETA_TERMS: dict[str, Any] = {
    **ALPHA_TERMS,
    "instrument_id": "synthetic-beta",
    "issuer_id": "SYNBANK-BETA",
    "issuer_name": "Synthetic Bank Beta",
    "instrument_name": "Synthetic Bank Beta 7.250% Perpetual AT1",
    "issue_date": date(2021, 6, 30),
    "current_coupon_rate": 0.0725,
    "coupon_frequency": "quarterly",
    "day_count": "ACT_365",
    "first_call_date": date(2028, 6, 30),
    "subsequent_call_frequency_months": 12,
    "reset_benchmark": "EURIBOR_3M",
    "reset_margin_bps": 512.5,
    "contractual_cet1_trigger": 0.07,
    "loss_absorption_type": "equity_conversion",
}


def make_instrument(**overrides: Any) -> AT1Instrument:
    """Build a valid instrument from ALPHA_TERMS with selected overrides."""
    return AT1Instrument.model_validate({**ALPHA_TERMS, **overrides})


@pytest.fixture
def alpha_instrument() -> AT1Instrument:
    """Semiannual fixed-to-reset instrument (5y first call, 5y subsequent calls)."""
    return AT1Instrument.model_validate(ALPHA_TERMS)


@pytest.fixture
def beta_instrument() -> AT1Instrument:
    """Quarterly fixed-to-reset instrument (7y first call, annual subsequent calls)."""
    return AT1Instrument.model_validate(BETA_TERMS)


@pytest.fixture
def repo_instruments_dir() -> Path:
    """The repository's sample instruments directory."""
    return REPO_ROOT / "data" / "instruments"


@pytest.fixture
def repo_scenarios_file() -> Path:
    """The repository's sample scenario file."""
    return REPO_ROOT / "data" / "scenarios" / "basic_scenarios.yaml"
