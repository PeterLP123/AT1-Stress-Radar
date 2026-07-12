"""Typed domain model for stress scenarios.

The scenario fields defined here are **placeholders for a future decomposition
engine**. The current application only validates the scenario file format so
that later work has a stable schema to build on; it does not yet apply the
shocks to a valuation.

Conventions
-----------
- All ``*_shock_bps`` fields are basis points and are intended to be converted
  downstream with ``bps / 10_000``.
- ``issuer_equity_shock`` and ``cet1_ratio_shock`` are decimals: ``-0.30``
  means the issuer's equity falls 30%; ``-0.02`` means the CET1 ratio falls by
  2 percentage points.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CallState(StrEnum):
    """Deterministic call states supported by the state-pricing model."""

    CALLED_AT_FIRST_CALL = "called_at_first_call"
    EXTENDED_TO_NEXT_CALL = "extended_to_next_call"


class Scenario(BaseModel):
    """A single named stress scenario (placeholder schema).

    ``call_assumption`` is a deterministic call state for now; a future
    version may replace it with a call probability.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_free_rate_shock_bps: float = Field(ge=-1_000, le=1_000)
    credit_spread_shock_bps: float = Field(ge=-2_000, le=2_000)
    reset_rate_shock_bps: float = Field(ge=-1_000, le=1_000)
    call_assumption: CallState
    issuer_equity_shock: float | None = Field(
        default=None, ge=-1, le=1, description="Optional equity return shock as a decimal."
    )
    cet1_ratio_shock: float | None = Field(
        default=None,
        ge=-0.2,
        le=0.2,
        description="Optional additive shock to the CET1 ratio, as a decimal.",
    )
