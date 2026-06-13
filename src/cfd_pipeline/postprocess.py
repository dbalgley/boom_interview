"""Postprocessing helpers for jet3D result files."""

from pathlib import Path

from cfd_pipeline.models import ForcesMoments


class InvalidResultFileError(Exception):
    """Raised when a jet3D output file does not contain valid result data."""


def parse_forces_moments_line(line: str) -> ForcesMoments:
    """Parse a jet3D forces/moments result line."""
    marker = "Final Forces and Moments"

    if marker not in line:
        raise InvalidResultFileError("line does not contain final forces and moments")

    parts = line.strip().split(":", maxsplit=1)
    if len(parts) != 2:
        raise InvalidResultFileError("result line is missing ':' separator")

    values = parts[1].strip(" []").split(",")
    if len(values) != 6:
        raise InvalidResultFileError(f"expected 6 result values, got {len(values)}")

    try:
        fx, fy, fz, mx, my, mz = (float(value) for value in values)
    except ValueError as exc:
        raise InvalidResultFileError("result values must be numeric") from exc

    return ForcesMoments(
        fx=fx,
        fy=fy,
        fz=fz,
        mx=mx,
        my=my,
        mz=mz,
    )


def parse_result_file(output_file: Path) -> ForcesMoments:
    """Parse final forces and moments from a jet3D output file."""
    try:
        lines = output_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise InvalidResultFileError(f"failed to read {output_file}: {exc}") from exc

    for line in lines:
        if "Final Forces and Moments" not in line:
            continue

        return parse_forces_moments_line(line)

    raise InvalidResultFileError(
        f"No results found in {output_file} — file may be truncated or invalid."
    )
