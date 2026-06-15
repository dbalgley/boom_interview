"""Filesystem helpers for CFD case inputs."""

import logging
from pathlib import Path
from typing import List

from cfd_pipeline.models import SimulationCase

logger = logging.getLogger("runner")


def write_case_input(case: SimulationCase, input_path: Path) -> None:
    """Write a jet3D input file for one simulation case.

    :param case: Simulation case parameters.
    :type case: SimulationCase
    :param input_path: Destination path for the generated input file.
    :type input_path: Path
    :returns: None
    """
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_text(
        (
            f"pressure={case.pressure}\n"
            f"temperature={case.temperature}\n"
            f"mach={case.mach}\n"
        ),
        encoding="utf-8",
    )


def parse_sweep_line(line: str) -> SimulationCase:
    """Parse one whitespace-delimited sweep row into a simulation case.

    :param line: One whitespace-delimited row from a sweep file.
    :type line: str
    :returns: The parsed simulation case.
    :rtype: SimulationCase
    :raises ValueError: If the row has the wrong number of columns or invalid values.
    """
    parts = line.strip().split()

    if len(parts) != 3:
        raise ValueError(f"expected 3 columns, got {len(parts)}")

    pressure_raw, temperature_raw, mach_raw = parts

    try:
        pressure = int(pressure_raw)
        temperature = float(temperature_raw)
        mach = float(mach_raw)
    except ValueError as exc:
        raise ValueError(
            "expected pressure=int, temperature=float, mach=float"
        ) from exc

    return SimulationCase(
        pressure=pressure,
        temperature=temperature,
        mach=mach,
    )


def read_sweep_file(sweep_path: Path) -> List[SimulationCase]:
    """Read a sweep input file, skipping malformed rows.

    :param sweep_path: Path to the sweep input file.
    :type sweep_path: Path
    :returns: Parsed simulation cases from valid lines.
    :rtype: list[SimulationCase]
    :raises OSError: If the file cannot be opened or read.
    """
    cases: List[SimulationCase] = []

    with sweep_path.open("r", encoding="utf-8") as sweep_file:
        lines = sweep_file.readlines()[1:]  # Skip header line

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        try:
            cases.append(parse_sweep_line(stripped))
        except ValueError:
            logger.warning("Skipping malformed line: %s", stripped)

    return cases
