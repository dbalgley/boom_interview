"""Command-line interface for the CFD workflow."""

import argparse
import logging
import sys
from pathlib import Path

from cfd_pipeline.logging_config import configure_logging
from cfd_pipeline.models import (
    DEFAULT_SOLVER_TIMEOUT_SECONDS,
    SimulationCase,
    SimulationStatus,
)
from cfd_pipeline.orchestrator import postprocess_result, run_single, run_sweep


def should_use_progress(*, no_progress: bool) -> bool:
    """Return whether an interactive progress display should be used."""
    return not no_progress and sys.stderr.isatty()


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dir",
        default="./cases",
        help="Directory to use for inputs and outputs",
    )
    parser.add_argument(
        "--sweep",
        type=str,
        help="Path to input.dat file for sweep of input cases",
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Generate and run a single input file",
    )
    parser.add_argument(
        "--pressure",
        type=int,
        help="Pressure value for single input",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Temperature value for single input",
    )
    parser.add_argument(
        "--mach",
        type=float,
        help="Mach value for single input",
    )
    parser.add_argument(
        "--postprocess",
        help="Postprocess a single result file by name",
    )
    parser.add_argument(
        "--solver",
        default="./bin/jet3D",
        help="Path to the jet3D solver executable",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable the progress bar for sweep runs.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_SOLVER_TIMEOUT_SECONDS,
        help=(
            "Maximum seconds to allow each solver run before marking it as "
            f"timed out. Default: {DEFAULT_SOLVER_TIMEOUT_SECONDS}."
        ),
    )

    return parser


def main() -> int:
    """Run the CFD workflow command-line interface."""
    parser = build_parser()
    args = parser.parse_args()

    progress_enabled = should_use_progress(no_progress=args.no_progress)

    configure_logging(use_tqdm=progress_enabled)
    logger = logging.getLogger("runner")

    if args.timeout <= 0:
        logger.error("ERROR: --timeout must be greater than 0")
        return 1

    case_dir = Path(args.dir)
    case_dir.mkdir(parents=True, exist_ok=True)

    solver_path = Path(args.solver)

    if args.single:
        if args.pressure is None or args.temperature is None or args.mach is None:
            logger.error(
                "ERROR: --pressure, --temperature, and"
                "--mach must be specified for single run"
            )
            return 1

        case = SimulationCase(
            pressure=args.pressure,
            temperature=args.temperature,
            mach=args.mach,
        )

        result = run_single(
            case=case,
            case_dir=case_dir,
            solver_path=solver_path,
            timeout_seconds=args.timeout,
        )
        return 0 if result.status == SimulationStatus.SUCCESS else 1

    if args.sweep:
        return run_sweep(
            sweep_path=Path(args.sweep),
            case_dir=case_dir,
            solver_path=solver_path,
            timeout_seconds=args.timeout,
            show_progress=progress_enabled,
        )

    if args.postprocess:
        return postprocess_result(case_dir / args.postprocess)

    logger.info(
        "No action specified. Use --single, --sweep INPUT.DAT, or --postprocess FILE"
    )
    return 1
