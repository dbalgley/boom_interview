"""Filesystem helpers for CFD case inputs."""

import logging
from pathlib import Path
from typing import List

from cfd_pipeline.models import SimulationCase

logger = logging.getLogger("runner")


def write_case_input(case: SimulationCase, input_path: Path) -> None:
    """Write a jet3D input file for one simulation case."""
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
    """Parse one whitespace-delimited sweep row into a simulation case."""
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
    """Read a sweep input file, skipping malformed rows."""
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
