"""Minimal Streamlit UI for AT1 Stress Radar.

All domain logic lives in the ``at1radar`` package; this module only wires
inputs to the pricing functions and renders the results.

Run from the repository root with::

    uv run streamlit run app/streamlit_app.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from at1radar.data.instrument_loader import InstrumentLoadError, load_instruments
from at1radar.domain.instruments import AT1Instrument
from at1radar.domain.scenarios import CallState
from at1radar.pricing.state_pricing import value_both_states

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTRUMENTS_DIR = REPO_ROOT / "data" / "instruments"
DEFAULT_VALUATION_DATE = date(2026, 6, 30)

_TERMS_ROWS: list[tuple[str, str]] = [
    ("Instrument ID", "instrument_id"),
    ("Issuer", "issuer_name"),
    ("Currency", "currency"),
    ("Issue date", "issue_date"),
    ("Notional", "notional"),
    ("Current coupon", "current_coupon_rate"),
    ("Coupon frequency", "coupon_frequency"),
    ("Day count", "day_count"),
    ("First call date", "first_call_date"),
    ("Subsequent call frequency (months)", "subsequent_call_frequency_months"),
    ("Reset benchmark", "reset_benchmark"),
    ("Reset margin (bps)", "reset_margin_bps"),
    ("CET1 trigger", "contractual_cet1_trigger"),
    ("Loss absorption", "loss_absorption_type"),
    ("Coupon discretion", "coupon_discretion"),
    ("Governing law", "governing_law"),
]


def _terms_table(instrument: AT1Instrument) -> dict[str, str]:
    """Key contractual terms as a display-friendly mapping."""
    formatted: dict[str, str] = {}
    for label, field in _TERMS_ROWS:
        value = getattr(instrument, field)
        if field in ("current_coupon_rate", "contractual_cet1_trigger"):
            formatted[label] = f"{value:.4%}"
        elif field == "notional":
            formatted[label] = f"{value:,.0f}"
        else:
            formatted[label] = str(getattr(value, "value", value))
    return formatted


def main() -> None:
    """Render the app."""
    st.set_page_config(page_title="AT1 Stress Radar", layout="wide")
    st.title("AT1 Stress Radar")
    st.warning(
        "**Research prototype.** All instrument data is synthetic and the valuation "
        "model is deliberately simplified (flat discount rate, constant reset "
        "benchmark, deterministic call states). Outputs are research illustrations, "
        "not investment recommendations, fair values, or executable prices."
    )

    try:
        instruments = load_instruments(INSTRUMENTS_DIR)
    except InstrumentLoadError as exc:
        st.error(f"Failed to load instruments: {exc}")
        return

    with st.sidebar:
        st.header("Inputs")
        instrument = st.selectbox(
            "Instrument",
            instruments,
            format_func=lambda i: f"{i.instrument_name} ({i.instrument_id})",
        )
        valuation_date = st.date_input(
            "Valuation date",
            value=DEFAULT_VALUATION_DATE,
            min_value=instrument.issue_date,
            help="Must be before the instrument's first call date.",
        )
        flat_discount_rate = st.number_input(
            "Flat discount rate (decimal)",
            min_value=0.0,
            max_value=0.5,
            value=0.08,
            step=0.005,
            format="%.4f",
            help="Single flat annual rate used to discount all cash flows. 0.08 = 8%.",
        )
        assumed_reset_rate = st.number_input(
            "Assumed reset benchmark rate (decimal)",
            min_value=0.0,
            max_value=0.2,
            value=0.03,
            step=0.0025,
            format="%.4f",
            help="Benchmark rate assumed constant after the first reset. 0.03 = 3%.",
        )

    st.subheader("Contractual terms")
    st.table(_terms_table(instrument))

    try:
        results = value_both_states(
            instrument=instrument,
            valuation_date=valuation_date,
            flat_discount_rate=flat_discount_rate,
            assumed_reset_benchmark_rate=assumed_reset_rate,
        )
    except ValueError as exc:
        st.error(f"Cannot value instrument with these inputs: {exc}")
        return

    called = results[CallState.CALLED_AT_FIRST_CALL]
    extended = results[CallState.EXTENDED_TO_NEXT_CALL]

    st.subheader("Simplified state values")
    col_called, col_extended, col_diff = st.columns(3)
    col_called.metric(
        f"Called at first call ({called.terminal_date})",
        f"{called.model_price_pct_of_notional:.3f}% of notional",
        help=f"PV {called.present_value:,.2f} {instrument.currency.value}",
    )
    col_extended.metric(
        f"Extended to next call ({extended.terminal_date})",
        f"{extended.model_price_pct_of_notional:.3f}% of notional",
        help=f"PV {extended.present_value:,.2f} {instrument.currency.value}",
    )
    col_diff.metric(
        "Extension impact (extended - called)",
        f"{extended.model_price_pct_of_notional - called.model_price_pct_of_notional:+.3f} pts",
        help=(
            f"PV difference {extended.present_value - called.present_value:+,.2f} "
            f"{instrument.currency.value}"
        ),
    )

    st.subheader("Cash flows")
    state_label = st.radio(
        "State",
        [state.value for state in CallState],
        horizontal=True,
    )
    selected = results[CallState(state_label)]
    st.dataframe(selected.cashflows, hide_index=True, width="stretch")
    st.caption(
        f"Assumptions: {selected.assumptions}. Post-reset coupons pay the assumed "
        "benchmark plus the contractual reset margin (bps / 10,000)."
    )


if __name__ == "__main__":
    main()
