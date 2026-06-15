"""Tests for CFD workflow orchestration."""

import logging
from pathlib import Path

import pytest

import cfd_pipeline.orchestrator as orchestrator
from cfd_pipeline.models import SimulationCase, SimulationResult, SimulationStatus


def test_run_single_writes_input_and_returns_success(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Write input and return success when solver output is valid."""
    case = SimulationCase(pressure=101325, temperature=288.15, mach=0.85)

    def fake_run_solver(
        *,
        case: SimulationCase,
        input_path: Path,
        output_path: Path,
        solver_path: Path,
    ) -> SimulationResult:
        output_path.write_text(
            "CFD Solver Output Log\n"
            "======================\n"
            "Final Forces and Moments (N, Nm): "
            "[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]\n",
            encoding="utf-8",
        )

        return SimulationResult(
            case=case,
            status=SimulationStatus.SUCCESS,
            input_path=input_path,
            output_path=output_path,
            stdout="[solver] success: {'status': 'ok'}",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(orchestrator, "run_solver", fake_run_solver)

    result = orchestrator.run_single(
        case=case,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert result.status == SimulationStatus.SUCCESS
    assert result.returncode == 0
    assert (tmp_path / "input_case_m0.85_p101325_t288.15.txt").exists()
    assert (tmp_path / "result_case_m0.85_p101325_t288.15.log").exists()


def test_run_single_returns_failure_for_solver_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Return FAILED when the solver process fails."""
    caplog.set_level(logging.ERROR, logger="runner")
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

    result = orchestrator.run_single(
        case=case,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert result.status == SimulationStatus.FAILED
    assert result.returncode == 1
    assert "Floating point exception" in result.stderr
    assert "ERROR running case" in caplog.text


def test_run_single_returns_failure_for_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Return TIMEOUT when the solver times out."""
    caplog.set_level(logging.ERROR, logger="runner")
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

    result = orchestrator.run_single(
        case=case,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert result.status == SimulationStatus.TIMEOUT
    assert result.returncode is None
    assert "TIMEOUT running case" in caplog.text


def test_run_single_returns_failure_for_invalid_solver_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Return INVALID_OUTPUT when solver succeeds but output is invalid."""
    caplog.set_level(logging.ERROR, logger="runner")
    case = SimulationCase(pressure=100000, temperature=300.0, mach=1.5)

    def fake_run_solver(
        *,
        case: SimulationCase,
        input_path: Path,
        output_path: Path,
        solver_path: Path,
    ) -> SimulationResult:
        output_path.write_text(
            "CFD Solver Output Log\n"
            "======================\n"
            "ERROR: Simulation terminated unexpectedly during write.\n",
            encoding="utf-8",
        )

        return SimulationResult(
            case=case,
            status=SimulationStatus.SUCCESS,
            input_path=input_path,
            output_path=output_path,
            stdout="[solver] success: {'status': 'incomplete_output'}",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(orchestrator, "run_solver", fake_run_solver)

    result = orchestrator.run_single(
        case=case,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
    )

    assert result.status == SimulationStatus.INVALID_OUTPUT
    assert result.returncode == 0
    assert "No results found" in result.stderr
    assert "solver produced invalid output" in caplog.text


def test_run_sweep_continues_after_failed_case(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Continue running sweep cases after a failure."""
    sweep_path = tmp_path / "input.dat"
    sweep_path.write_text(
        "pressure temperature mach\n101325 288.15 0.85\n100000 300.0 1.5\n",
        encoding="utf-8",
    )

    calls: list[SimulationCase] = []

    def fake_run_single(
        *,
        case: SimulationCase,
        case_dir: Path,
        solver_path: Path,
    ) -> SimulationResult:
        calls.append(case)

        status = (
            SimulationStatus.FAILED if len(calls) == 1 else SimulationStatus.SUCCESS
        )

        return SimulationResult(
            case=case,
            status=status,
            input_path=case.input_path(case_dir),
            output_path=case.output_path(case_dir),
            stdout="",
            stderr="solver failed" if status == SimulationStatus.FAILED else "",
            returncode=1 if status == SimulationStatus.FAILED else 0,
        )

    monkeypatch.setattr(orchestrator, "run_single", fake_run_single)

    exit_code = orchestrator.run_sweep(
        sweep_path=sweep_path,
        case_dir=tmp_path,
        solver_path=Path("./bin/jet3D"),
        show_progress=False,
    )

    assert exit_code == 1
    assert len(calls) == 2


def test_run_sweep_returns_failure_for_missing_sweep_file(tmp_path: Path) -> None:
    """Return a failure exit code when the specified sweep file does not exist."""
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
    """Correctly read the output file, extract forces and moments, and log them."""
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
    """Return a failure exit code when the specified output file does not exist."""
    exit_code = orchestrator.postprocess_result(tmp_path / "missing.log")

    assert exit_code == 1
