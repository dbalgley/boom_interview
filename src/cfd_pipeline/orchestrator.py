"""Workflow orchestration for jet3D simulation runs."""

import logging
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Counter, Union

from tqdm import tqdm

from cfd_pipeline.case_io import read_sweep_file, write_case_input
from cfd_pipeline.models import SimulationCase, SimulationResult, SimulationStatus
from cfd_pipeline.postprocess import InvalidResultFileError, parse_result_file
from cfd_pipeline.solver import run_solver

runner_logger = logging.getLogger("runner")
postprocess_logger = logging.getLogger("postprocess")
solver_stdout_logger = logging.getLogger("solver.stdout")
solver_stderr_logger = logging.getLogger("solver.stderr")


def _log_process_streams(stdout: Union[bytes, str], stderr: Union[bytes, str]) -> None:
    """Forward solver output without modifying solver-emitted text."""
    for line in stdout.splitlines():
        solver_stdout_logger.info("%s", line)

    for line in stderr.splitlines():
        solver_stderr_logger.error("%s", line)


def run_single(
    *,
    case: SimulationCase,
    case_dir: Path,
    solver_path: Path,
) -> SimulationResult:
    """Run one simulation case and return its workflow result."""
    input_path = case.input_path(case_dir)
    output_path = case.output_path(case_dir)

    write_case_input(case=case, input_path=input_path)

    runner_logger.info("Running case %s...", case.case_name)

    result = run_solver(
        case=case,
        input_path=input_path,
        output_path=output_path,
        solver_path=solver_path,
    )

    _log_process_streams(stdout=result.stdout, stderr=result.stderr)

    if result.status == SimulationStatus.TIMEOUT:
        runner_logger.error("TIMEOUT running case %s", case.case_name)
        return result

    if result.status == SimulationStatus.FAILED:
        runner_logger.error(
            "ERROR running case %s: %s",
            case.case_name,
            result.stderr.strip() or "solver failed",
        )
        return result

    try:
        parse_result_file(output_path)
    except InvalidResultFileError as exc:
        invalid_result = SimulationResult(
            case=case,
            status=SimulationStatus.INVALID_OUTPUT,
            input_path=input_path,
            output_path=output_path,
            stdout=result.stdout,
            stderr=str(exc),
            returncode=result.returncode,
        )

        runner_logger.error(
            "ERROR running case %s: solver produced invalid output: %s",
            case.case_name,
            invalid_result.stderr,
        )

        return invalid_result

    runner_logger.info(
        "SUCCESS input: %s, output:%s",
        input_path,
        output_path,
    )

    return result


def run_sweep(
    *,
    sweep_path: Path,
    case_dir: Path,
    solver_path: Path,
    show_progress: bool = True,
) -> int:
    """Run a sweep of simulation cases."""
    try:
        cases = read_sweep_file(sweep_path)
    except OSError:
        runner_logger.error("ERROR: sweep file not found %s", sweep_path)
        return 1

    status_counts: Counter[SimulationStatus] = Counter()
    progress_enabled = show_progress and sys.stderr.isatty()

    progress_bar = (
        tqdm(cases, desc="Running sweep", unit="case") if progress_enabled else None
    )

    case_iterable: Iterable[SimulationCase]
    case_iterable = progress_bar if progress_bar is not None else cases

    try:
        for case in case_iterable:
            result = run_single(
                case=case,
                case_dir=case_dir,
                solver_path=solver_path,
            )

            status_counts[result.status] += 1

            if progress_bar is not None:
                progress_bar.set_postfix(
                    {
                        "success": status_counts[SimulationStatus.SUCCESS],
                        "failed": status_counts[SimulationStatus.FAILED],
                        "timeout": status_counts[SimulationStatus.TIMEOUT],
                        "invalid": status_counts[SimulationStatus.INVALID_OUTPUT],
                    }
                )
    finally:
        if progress_bar is not None:
            progress_bar.close()

    total = sum(status_counts.values())

    runner_logger.info(
        (
            "Sweep complete: %s success, %s failed, %s timeout, "
            "%s invalid output, %s total"
        ),
        status_counts[SimulationStatus.SUCCESS],
        status_counts[SimulationStatus.FAILED],
        status_counts[SimulationStatus.TIMEOUT],
        status_counts[SimulationStatus.INVALID_OUTPUT],
        total,
    )

    return 0 if status_counts[SimulationStatus.SUCCESS] == total else 1


def postprocess_result(output_file: Path) -> int:
    """Postprocess one result file and log parsed values."""
    if not output_file.exists():
        postprocess_logger.error("File not found: %s", output_file)
        return 1

    try:
        result = parse_result_file(output_file)
    except InvalidResultFileError as exc:
        postprocess_logger.error("%s", exc)
        return 1

    postprocess_logger.info("Fx (N): %s", result.fx)
    postprocess_logger.info("Fy (N): %s", result.fy)
    postprocess_logger.info("Fz (N): %s", result.fz)
    postprocess_logger.info("Mx (Nm): %s", result.mx)
    postprocess_logger.info("My (Nm): %s", result.my)
    postprocess_logger.info("Mz (Nm): %s", result.mz)

    return 0
