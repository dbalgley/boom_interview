"""Tests for CFD workflow data models."""

from pathlib import Path

from cfd_pipeline.models import SimulationCase


def test_simulation_case_generates_legacy_case_name() -> None:
    """Test that case_name generates a stable identifier for input and output files."""
    case = SimulationCase(
        pressure=101325,
        temperature=288.15,
        mach=0.85,
    )

    assert case.case_name == "m0.85_p101325_t288.15"


def test_simulation_case_generates_input_path() -> None:
    """Test that the input_path generates the expected input file path for a case."""
    case = SimulationCase(
        pressure=101325,
        temperature=288.15,
        mach=0.85,
    )

    assert case.input_path(Path("cases")) == Path(
        "cases/input_case_m0.85_p101325_t288.15.txt"
    )


def test_simulation_case_generates_output_path() -> None:
    """Test that the output_path generates the expected output file path for a case."""
    case = SimulationCase(
        pressure=101325,
        temperature=288.15,
        mach=0.85,
    )

    assert case.output_path(Path("cases")) == Path(
        "cases/result_case_m0.85_p101325_t288.15.log"
    )
