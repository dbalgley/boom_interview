"""Tests for CFD workflow orchestration."""

from pathlib import Path
from typing import List

import cfd_pipeline.orchestrator as orchestrator
import pytest
from cfd_pipeline.models import SimulationCase, SimulationResult, SimulationStatus


def test_run_single_writes_input_and_returns_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that run_single generates the correct input file and returns a success exit code when the solver returns a successful result."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)
    solver_path = Path("./bin/jet3D")

    def fake_run_solver(
        *,
        case: SimulationCase,
        input_path: Path,
        output_path: Path,
        solver_path: Path,
    ) -> SimulationResult:
        return SimulationResult(
            case=case,
            status=SimulationStatus.SUCCESS,
            input_path=input_path,
            output_path=output_path,
            stdout="[solver] success: {'status': 'done'}\n",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(orchestrator, "run_solver", fake_run_solver)

    exit_code = orchestrator.run_single(
        case=case,
        case_dir=tmp_path,
        solver_path=solver_path,
    )

    assert exit_code == 0
    assert case.input_path(tmp_path).read_text(encoding="utf-8") == (
        "pressure=101325\n" "temperature=288.15\n" "mach=0.85\n"
    )


def test_run_single_returns_failure_for_solver_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that run_single returns a failure exit code when the solver returns an error result (e.g. non-zero exit code)."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)

    def fake_run_solver(
        *,
        case: SimulationCase,
        input_path: Path,
        output_path: Path,
        solver_path: Path,
    ) -> SimulationResult:
        return SimulationResult(
            case=case,
            status=SimulationStatus.FAILED,
            input_path=input_path,
            output_path=output_path,
            stdout="",
            stderr="[solver error] Floating point exception\n",
            returncode=1,
        )

    monkeypatch.setattr(orchestrator, "run_solver", fake_run_solver)

    exit_code = orchestrator.run_single(
        case=case,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert exit_code == 1


def test_run_single_returns_failure_for_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that run_single returns a failure exit code when the solver returns a timeout result."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)

    def fake_run_solver(
        *,
        case: SimulationCase,
        input_path: Path,
        output_path: Path,
        solver_path: Path,
    ) -> SimulationResult:
        return SimulationResult(
            case=case,
            status=SimulationStatus.TIMEOUT,
            input_path=input_path,
            output_path=output_path,
            stdout="",
            stderr="",
            returncode=None,
        )

    monkeypatch.setattr(orchestrator, "run_solver", fake_run_solver)

    exit_code = orchestrator.run_single(
        case=case,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert exit_code == 1


def test_run_sweep_continues_after_failed_case(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that run_sweep continues running remaining cases even if one case fails, and that it returns a failure exit code if any case fails."""
    sweep_path = tmp_path / "input.dat"
    sweep_path.write_text(
        ("pressure temperature mach\n" "101325 288.15 0.85\n" "90000 275.0 1.2\n"),
        encoding="utf-8",
    )

    calls: List[str] = []

    def fake_run_single(
        *,
        case: SimulationCase,
        case_dir: Path,
        solver_path: Path,
    ) -> int:
        calls.append(case.case_name)
        if case.pressure == 101325:
            return 1
        return 0

    monkeypatch.setattr(orchestrator, "run_single", fake_run_single)

    exit_code = orchestrator.run_sweep(
        sweep_path=sweep_path,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert exit_code == 1
    assert calls == [
        "m0.85_p101325_t288.15",
        "m1.2_p90000_t275.0",
    ]


def test_run_sweep_returns_failure_for_missing_sweep_file(tmp_path: Path) -> None:
    """Test that run_sweep returns a failure exit code when the specified sweep file does not exist."""
    exit_code = orchestrator.run_sweep(
        sweep_path=tmp_path / "missing.dat",
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert exit_code == 1


def test_postprocess_result_logs_values(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that postprocess_result correctly reads the output file, extracts forces and moments, and logs them."""
    caplog.set_level("INFO", logger="postprocess")

    output_file = tmp_path / "result.log"
    output_file.write_text(
        "Final Forces and Moments (N, Nm): [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]\n",
        encoding="utf-8",
    )

    exit_code = orchestrator.postprocess_result(output_file)

    assert exit_code == 0
    assert "Fx (N): 1.0" in caplog.text
    assert "Mz (Nm): 6.0" in caplog.text


def test_postprocess_result_returns_failure_for_missing_file(tmp_path: Path) -> None:
    """Test that postprocess_result returns a failure exit code when the specified output file does not exist."""
    exit_code = orchestrator.postprocess_result(tmp_path / "missing.log")

    assert exit_code == 1
