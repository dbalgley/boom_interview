"""Tests for case input/output helpers."""

from pathlib import Path

import pytest
from cfd_pipeline.case_io import parse_sweep_line, read_sweep_file, write_case_input
from cfd_pipeline.models import SimulationCase


def test_write_case_input_writes_expected_solver_input(tmp_path: Path) -> None:
    """Test that write_case_input generates the expected input file content for a case."""
    case = SimulationCase(
        pressure=101325,
        temperature=288.15,
        mach=0.85,
    )
    input_path = tmp_path / "input_case.txt"

    write_case_input(case, input_path)

    assert input_path.read_text(encoding="utf-8") == (
        "pressure=101325\n" "temperature=288.15\n" "mach=0.85\n"
    )


def test_parse_sweep_line_returns_simulation_case() -> None:
    """Test that parse_sweep_line correctly parses a valid sweep line into a SimulationCase."""
    case = parse_sweep_line("101325 288.15 0.85")

    assert case == SimulationCase(
        pressure=101325,
        temperature=288.15,
        mach=0.85,
    )


def test_parse_sweep_line_rejects_wrong_column_count() -> None:
    """Test that parse_sweep_line raises an error if the line does not have exactly 3 columns."""
    with pytest.raises(ValueError, match="expected 3 columns"):
        parse_sweep_line("101325 288.15")


def test_parse_sweep_line_rejects_non_numeric_values() -> None:
    """Test that parse_sweep_line raises an error if the values cannot be parsed as the expected types."""
    with pytest.raises(ValueError, match="expected pressure=int"):
        parse_sweep_line("not-pressure 288.15 0.85")


def test_read_sweep_file_skips_header_and_returns_valid_cases(tmp_path: Path) -> None:
    """Test that read_sweep_file correctly reads a sweep file, skipping the header and returning valid cases."""
    sweep_path = tmp_path / "input.dat"
    sweep_path.write_text(
        ("pressure temperature mach\n" "101325 288.15 0.85\n" "90000 275.0 1.2\n"),
        encoding="utf-8",
    )

    cases = read_sweep_file(sweep_path)

    assert cases == [
        SimulationCase(pressure=101325, temperature=288.15, mach=0.85),
        SimulationCase(pressure=90000, temperature=275.0, mach=1.2),
    ]


def test_read_sweep_file_skips_malformed_lines(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that read_sweep_file skips malformed lines and logs a warning for each skipped line."""
    sweep_path = tmp_path / "input.dat"
    sweep_path.write_text(
        (
            "pressure temperature mach\n"
            "101325 288.15 0.85\n"
            "this is bad\n"
            "90000 275.0 1.2\n"
        ),
        encoding="utf-8",
    )

    cases = read_sweep_file(sweep_path)

    assert cases == [
        SimulationCase(pressure=101325, temperature=288.15, mach=0.85),
        SimulationCase(pressure=90000, temperature=275.0, mach=1.2),
    ]
    assert "Skipping malformed line: this is bad" in caplog.text
