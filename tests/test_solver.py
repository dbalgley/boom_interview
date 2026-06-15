"""Tests for jet3D solver execution wrapper."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from cfd_pipeline.models import SimulationCase, SimulationStatus
from cfd_pipeline.solver import run_solver


def test_run_solver_returns_success_result(monkeypatch: Any, tmp_path: Path) -> None:
    """Returns a SUCCESS when subprocess.run completes with a zero exit code."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.log"
    solver_path = Path("./bin/jet3D")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Simulate a successful solver run with specific stdout and stderr."""
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="[solver] success: {'status': 'done'}\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_solver(
        case=case,
        input_path=input_path,
        output_path=output_path,
        solver_path=solver_path,
        timeout_seconds=60,
    )

    assert result.status == SimulationStatus.SUCCESS
    assert result.returncode == 0
    assert result.stdout == "[solver] success: {'status': 'done'}\n"
    assert result.stderr == ""
    assert result.input_path == input_path
    assert result.output_path == output_path


def test_run_solver_returns_failed_result_for_nonzero_exit(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """Return a failed result when subprocess.run returns a non-zero exit code."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.log"
    solver_path = Path("./bin/jet3D")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=1,
            stdout="",
            stderr="[solver error] Floating point exception\n",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_solver(
        case=case,
        input_path=input_path,
        output_path=output_path,
        solver_path=solver_path,
        timeout_seconds=60,
    )

    assert result.status == SimulationStatus.FAILED
    assert result.returncode == 1
    assert result.stderr == "[solver error] Floating point exception\n"


def test_run_solver_returns_timeout_result(monkeypatch: Any, tmp_path: Path) -> None:
    """Return a timeout result when subprocess.run raises TimeoutExpired."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.log"
    solver_path = Path("./bin/jet3D")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=300,
            output="partial stdout",
            stderr="partial stderr",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_solver(
        case=case,
        input_path=input_path,
        output_path=output_path,
        solver_path=solver_path,
    )

    assert result.status == SimulationStatus.TIMEOUT
    assert result.returncode is None
    assert result.stdout == "partial stdout"
    assert result.stderr == "partial stderr"


def test_run_solver_returns_failed_result_for_os_error(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    """Return FAILED when subprocess.run raises an OSError."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.log"
    solver_path = Path("./bin/missing_solver")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise PermissionError("permission denied")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_solver(
        case=case,
        input_path=input_path,
        output_path=output_path,
        solver_path=solver_path,
    )

    assert result.status == SimulationStatus.FAILED
    assert result.returncode is None
    assert "permission denied" in result.stderr
