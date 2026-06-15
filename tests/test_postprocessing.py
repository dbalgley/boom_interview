"""Tests for jet3D result postprocessing."""

from pathlib import Path

import pytest

from cfd_pipeline.models import ForcesMoments
from cfd_pipeline.postprocess import (
    InvalidResultFileError,
    parse_forces_moments_line,
    parse_result_file,
)


def test_parse_forces_moments_line_returns_values() -> None:
    """Test that parse_forces_moments_line correctly parses a valid result line."""
    line = "Final Forces and Moments (N, Nm): [-1.0, 2.5, 3.0, -4.0, 5.25, 6.0]"

    result = parse_forces_moments_line(line)

    assert result == ForcesMoments(
        fx=-1.0,
        fy=2.5,
        fz=3.0,
        mx=-4.0,
        my=5.25,
        mz=6.0,
    )


def test_parse_forces_moments_line_rejects_wrong_value_count() -> None:
    """Reject a result line with the wrong number of values."""
    line = "Final Forces and Moments (N, Nm): [1, 2, 3]"

    with pytest.raises(
        InvalidResultFileError,
        match="expected 6 force/moment values, got 3",
    ):
        parse_forces_moments_line(line)


def test_parse_forces_moments_line_rejects_non_numeric_values() -> None:
    """Reject a result line with non-numeric values."""
    line = "Final Forces and Moments (N, Nm): [1, 2, nope, 4, 5, 6]"

    with pytest.raises(
        InvalidResultFileError,
        match="force/moment values must be numeric",
    ):
        parse_forces_moments_line(line)


def test_parse_result_file_returns_values_from_complete_output(tmp_path: Path) -> None:
    """Correctly parse a valid result line from a complete output file."""
    output_file = tmp_path / "result.log"
    output_file.write_text(
        (
            "CFD Solver Output Log\n"
            "======================\n\n"
            "INFO: Step 0 converged in 0.01s\n"
            "\n--- Solver Statistics ---\n"
            "Final Forces and Moments (N, Nm): [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]\n"
            "--------------------------\n"
        ),
        encoding="utf-8",
    )

    result = parse_result_file(output_file)

    assert result == ForcesMoments(
        fx=1.0,
        fy=2.0,
        fz=3.0,
        mx=4.0,
        my=5.0,
        mz=6.0,
    )


def test_parse_result_file_rejects_truncated_output(tmp_path: Path) -> None:
    """
    Test that error is raised if the output file does not contain a valid result line.

    This may indicate a truncated or otherwise invalid output file.
    """
    output_file = tmp_path / "truncated.log"
    output_file.write_text(
        (
            "CFD Solver Output Log\n"
            "======================\n\n"
            "INFO: Step 0 converged in 0.01s\n"
            "ERROR: Simulation terminated unexpectedly during write.\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(InvalidResultFileError, match="No results found"):
        parse_result_file(output_file)


def test_parse_result_file_rejects_missing_file(tmp_path: Path) -> None:
    """Raise an error if the output file does not exist or cannot be read."""
    """Test that parse_result_file raises an error if the output file does not exist."""
    output_file = tmp_path / "missing.log"

    with pytest.raises(InvalidResultFileError, match="failed to read"):
        parse_result_file(output_file)


def test_parse_forces_moments_line_rejects_missing_colon() -> None:
    """Raise an error if the result line is missing the ':' separator."""
    line = "Final Forces and Moments (N, Nm) [1, 2, 3, 4, 5, 6]"

    with pytest.raises(InvalidResultFileError, match="missing ':' separator"):
        parse_forces_moments_line(line)


def test_parse_forces_moments_line_rejects_missing_brackets() -> None:
    """Raise and error if the result line is missing brackets around the values."""
    line = "Final Forces and Moments (N, Nm): 1, 2, 3, 4, 5, 6"

    with pytest.raises(InvalidResultFileError, match="missing bracketed values"):
        parse_forces_moments_line(line)


def test_parse_forces_moments_line_rejects_extra_values() -> None:
    """Raise an error if the result line contains more than 6 values."""
    line = "Final Forces and Moments (N, Nm): [1, 2, 3, 4, 5, 6, 7]"

    with pytest.raises(InvalidResultFileError, match="expected 6"):
        parse_forces_moments_line(line)


def test_parse_forces_moments_line_rejects_non_numeric_value() -> None:
    """Raise and error if values cannot be parsed as floats."""
    line = "Final Forces and Moments (N, Nm): [1, 2, nope, 4, 5, 6]"

    with pytest.raises(InvalidResultFileError, match="must be numeric"):
        parse_forces_moments_line(line)
