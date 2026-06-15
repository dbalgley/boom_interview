"""Postprocessing helpers for jet3D result files."""

import re
from pathlib import Path

from cfd_pipeline.models import ForcesMoments

RESULT_LINE_RE = re.compile(
    r"""
    ^\s*
    Final\s+Forces\s+and\s+Moments
    (?:\s*\(.*?\))?
    \s*:\s*
    \[
        (?P<values>[^\]]+)
    \]
    \s*$
    """,
    re.VERBOSE,
)


class InvalidResultFileError(ValueError):
    """Raised when a solver result file cannot be parsed."""


def parse_forces_moments_line(line: str) -> ForcesMoments:
    """
    Parse a solver result line into forces and moments.

    :param line: A solver line output that should contain forces and moments.
    :type line: str
    :returns: Parsed forces and moments values.
    :rtype: ForcesMoments
    :raises InvalidResultFileError: If the line cannot be parsed as expected.
    """
    match = RESULT_LINE_RE.match(line)

    if match is None:
        if "Final Forces and Moments" not in line:
            raise InvalidResultFileError(
                "result line does not contain 'Final Forces and Moments'"
            )

        if ":" not in line:
            raise InvalidResultFileError("result line is missing ':' separator")

        if "[" not in line or "]" not in line:
            raise InvalidResultFileError("result line is missing bracketed values")

        raise InvalidResultFileError("result line does not match expected format")

    raw_values = [value.strip() for value in match.group("values").split(",")]

    if len(raw_values) != 6:
        raise InvalidResultFileError(
            f"expected 6 force/moment values, got {len(raw_values)}"
        )

    try:
        values = [float(value) for value in raw_values]
    except ValueError as exc:
        raise InvalidResultFileError("force/moment values must be numeric") from exc

    return ForcesMoments(
        fx=values[0],
        fy=values[1],
        fz=values[2],
        mx=values[3],
        my=values[4],
        mz=values[5],
    )


def parse_result_file(output_file: Path) -> ForcesMoments:
    """Parse a solver output file.

    :param output_file: Path to the solver output file.
    :type output_file: Path
    :returns: Parsed forces and moments values.
    :rtype: ForcesMoments
    :raises InvalidResultFileError: If the file cannot be read or parsed.
    """
    try:
        lines = output_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InvalidResultFileError(
            f"failed to read result file {output_file}: {exc}"
        ) from exc

    for line in lines:
        if "Final Forces and Moments" in line:
            return parse_forces_moments_line(line)

    raise InvalidResultFileError(
        f"No results found in {output_file}; file may be truncated or invalid."
    )
