"""Command-line interface for AT1 Stress Radar.

Commands
--------
- ``at1radar validate``: validate all instrument and scenario YAML files.
- ``at1radar list-instruments``: list the instrument universe.
- ``at1radar price``: value one instrument under both call states.

Paths default to ``data/instruments`` and ``data/scenarios/basic_scenarios.yaml``
relative to the current working directory (i.e. run from the repository root),
and can be overridden with ``--instruments-dir`` / ``--scenarios-file``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from at1radar.data.instrument_loader import (
    DEFAULT_INSTRUMENTS_DIR,
    InstrumentLoadError,
    load_instruments,
)
from at1radar.data.scenario_loader import (
    DEFAULT_SCENARIOS_FILE,
    ScenarioLoadError,
    load_scenarios,
)
from at1radar.pricing.state_pricing import value_both_states


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``at1radar`` CLI."""
    parser = argparse.ArgumentParser(
        prog="at1radar",
        description="Research prototype for AT1 instruments (synthetic data only).",
    )
    parser.add_argument(
        "--instruments-dir",
        type=Path,
        default=DEFAULT_INSTRUMENTS_DIR,
        help="Directory containing instrument YAML files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser(
        "validate", help="Validate all instrument and scenario YAML files."
    )
    validate.add_argument(
        "--scenarios-file",
        type=Path,
        default=DEFAULT_SCENARIOS_FILE,
        help="Scenario YAML file to validate.",
    )

    subparsers.add_parser("list-instruments", help="List the instrument universe.")

    price = subparsers.add_parser(
        "price", help="Value one instrument under the called and extended states."
    )
    price.add_argument("--instrument", required=True, help="instrument_id to price.")
    price.add_argument(
        "--valuation-date",
        required=True,
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="Valuation date (from issue date up to, but not including, first call).",
    )
    price.add_argument(
        "--discount-rate",
        required=True,
        type=float,
        help="Flat annual discount rate as a decimal, e.g. 0.08 for 8%%.",
    )
    price.add_argument(
        "--reset-rate",
        required=True,
        type=float,
        help="Assumed reset benchmark rate as a decimal, e.g. 0.03 for 3%%.",
    )
    return parser


def _cmd_validate(args: argparse.Namespace) -> int:
    instruments = load_instruments(args.instruments_dir)
    print(f"OK: {len(instruments)} instrument(s) validated in {args.instruments_dir}")
    scenarios = load_scenarios(args.scenarios_file)
    print(f"OK: {len(scenarios)} scenario(s) validated in {args.scenarios_file}")
    return 0


def _cmd_list_instruments(args: argparse.Namespace) -> int:
    instruments = load_instruments(args.instruments_dir)
    for instrument in instruments:
        print(
            f"{instrument.instrument_id:<18} {instrument.issuer_name:<24} "
            f"{instrument.current_coupon_rate:.4%} {instrument.coupon_frequency.value:<10} "
            f"first call {instrument.first_call_date}"
        )
    return 0


def _cmd_price(args: argparse.Namespace) -> int:
    instruments = {i.instrument_id: i for i in load_instruments(args.instruments_dir)}
    if args.instrument not in instruments:
        raise InstrumentLoadError(
            f"unknown instrument '{args.instrument}'; available: {sorted(instruments)}"
        )
    instrument = instruments[args.instrument]
    results = value_both_states(
        instrument=instrument,
        valuation_date=args.valuation_date,
        flat_discount_rate=args.discount_rate,
        assumed_reset_benchmark_rate=args.reset_rate,
    )
    print(f"{instrument.instrument_name} ({instrument.instrument_id})")
    print(
        f"valuation date {args.valuation_date} | discount rate {args.discount_rate:.4%} "
        f"| assumed reset benchmark {args.reset_rate:.4%}"
    )
    print("Simplified model values (research illustration, not fair value):")
    for state, result in results.items():
        print(
            f"  {state.value:<24} terminal {result.terminal_date}  "
            f"PV {result.present_value:>14,.2f} {instrument.currency.value}  "
            f"price {result.model_price_pct_of_notional:>8.3f}% of notional  "
            f"({result.num_cashflows} cash flows)"
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)
    handlers = {
        "validate": _cmd_validate,
        "list-instruments": _cmd_list_instruments,
        "price": _cmd_price,
    }
    try:
        return handlers[args.command](args)
    except (InstrumentLoadError, ScenarioLoadError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
