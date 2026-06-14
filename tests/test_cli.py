"""Tests for the command-line interface."""

from pathlib import Path
from typing import List, Tuple

import pytest

import cfd_pipeline.cli as cli
from cfd_pipeline.models import SimulationCase


def test_main_returns_error_when_no_action(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return an error exit code when no action flags are provided."""
    monkeypatch.setattr("sys.argv", ["runner.py"])

    exit_code = cli.main()

    assert exit_code == 1


def test_main_returns_error_when_single_missing_required_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return an error exit code when required arguments are missing."""
    monkeypatch.setattr(
        "sys.argv",
        ["runner.py", "--single", "--pressure", "101325", "--temperature", "288.15"],
    )

    exit_code = cli.main()

    assert exit_code == 1


def test_main_routes_single_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test correct arguments when --single is specified with required parameters."""
    calls: List[Tuple[int, float, float, Path]] = []

    def fake_run_single(
        *,
        case: SimulationCase,
        case_dir: Path,
        solver_path: Path,
    ) -> int:
        calls.append((case.pressure, case.temperature, case.mach, case_dir))
        return 0

    monkeypatch.setattr(cli, "run_single", fake_run_single)
    monkeypatch.setattr(
        "sys.argv",
        [
            "runner.py",
            "--dir",
            str(tmp_path),
            "--single",
            "--pressure",
            "101325",
            "--temperature",
            "288.15",
            "--mach",
            "0.85",
        ],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert calls == [(101325, 288.15, 0.85, tmp_path)]


def test_main_routes_sweep(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Test correct arguments when --sweep is specified."""
    calls: List[Tuple[Path, Path]] = []

    def fake_run_sweep(*, sweep_path: Path, case_dir: Path, solver_path: Path) -> int:
        """Fake run_sweep that captures the arguments it was called with."""
        calls.append((sweep_path, case_dir))
        return 0

    monkeypatch.setattr(cli, "run_sweep", fake_run_sweep)
    monkeypatch.setattr(
        "sys.argv",
        ["runner.py", "--dir", str(tmp_path), "--sweep", "input.dat"],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert calls == [(Path("input.dat"), tmp_path)]


def test_main_routes_postprocess(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test correct arguments when --postprocess is specified."""
    calls: List[Path] = []

    def fake_postprocess_result(output_file: Path) -> int:
        calls.append(output_file)
        return 0

    monkeypatch.setattr(cli, "postprocess_result", fake_postprocess_result)
    monkeypatch.setattr(
        "sys.argv",
        ["runner.py", "--dir", str(tmp_path), "--postprocess", "result.log"],
    )

    exit_code = cli.main()

    assert exit_code == 0
    assert calls == [tmp_path / "result.log"]
