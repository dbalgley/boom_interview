"""Workflow orchestration for jet3D simulation runs."""

import logging
from pathlib import Path
from typing import Union

from cfd_pipeline.case_io import read_sweep_file, write_case_input
from cfd_pipeline.models import SimulationCase, SimulationStatus
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


def run_single(case: SimulationCase, case_dir: Path, solver_path: Path) -> int:
    """Generate input and run one simulation case."""
    input_path = case.input_path(case_dir)
    output_path = case.output_path(case_dir)

    write_case_input(case, input_path)

    runner_logger.info("Running case %s...", case.case_name)

    result = run_solver(
        case=case,
        input_path=input_path,
        output_path=output_path,
        solver_path=solver_path,
    )

    _log_process_streams(result.stdout, result.stderr)

    if result.status == SimulationStatus.SUCCESS:
        runner_logger.info("SUCCESS input: %s, output:%s", input_path, output_path)
        return 0

    if result.status == SimulationStatus.TIMEOUT:
        runner_logger.error("TIMEOUT on case %s", case.case_name)
        return 1

    runner_logger.error(
        "ERROR running case %s: %s",
        case.case_name,
        result.stderr.strip(),
    )
    return 1


def run_sweep(sweep_path: Path, case_dir: Path, solver_path: Path) -> int:
    """Run all valid cases from a sweep file."""
    try:
        cases = read_sweep_file(sweep_path)
    except FileNotFoundError:
        runner_logger.error("ERROR: Sweep file not found: %s", sweep_path)
        return 1

    exit_code = 0

    for case in cases:
        case_exit_code = run_single(
            case=case,
            case_dir=case_dir,
            solver_path=solver_path,
        )

        if case_exit_code != 0:
            exit_code = 1

    return exit_code


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
