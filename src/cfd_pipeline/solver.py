"""Execution wrapper for the jet3D solver."""

import subprocess
from pathlib import Path

from cfd_pipeline.models import (
    DEFAULT_SOLVER_TIMEOUT_SECONDS,
    SimulationCase,
    SimulationResult,
    SimulationStatus,
)


def run_solver(
    case: SimulationCase,
    input_path: Path,
    output_path: Path,
    solver_path: Path,
    timeout_seconds: int = DEFAULT_SOLVER_TIMEOUT_SECONDS,
) -> SimulationResult:
    """Run the jet3D solver for one simulation case.

    :param case: Simulation case to run.
    :type case: SimulationCase
    :param input_path: Path to the solver input file.
    :type input_path: Path
    :param output_path: Path where the solver should write its output.
    :type output_path: Path
    :param solver_path: Path to the jet3D solver executable.
    :type solver_path: Path
    :param timeout_seconds: Maximum allowed time per solver run in seconds.
    :type timeout_seconds: int
    :returns: Result of running the solver, including status and I/O.
    :rtype: SimulationResult
    """
    try:
        completed_process = subprocess.run(
            [str(solver_path), str(input_path), str(output_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return SimulationResult(
            case=case,
            status=SimulationStatus.TIMEOUT,
            input_path=input_path,
            output_path=output_path,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            returncode=None,
        )
    except OSError as exc:
        return SimulationResult(
            case=case,
            status=SimulationStatus.FAILED,
            input_path=input_path,
            output_path=output_path,
            stdout="",
            stderr=str(exc),
            returncode=None,
        )

    if completed_process.returncode != 0:
        return SimulationResult(
            case=case,
            status=SimulationStatus.FAILED,
            input_path=input_path,
            output_path=output_path,
            stdout=completed_process.stdout,
            stderr=completed_process.stderr,
            returncode=completed_process.returncode,
        )

    return SimulationResult(
        case=case,
        status=SimulationStatus.SUCCESS,
        input_path=input_path,
        output_path=output_path,
        stdout=completed_process.stdout,
        stderr=completed_process.stderr,
        returncode=completed_process.returncode,
    )
