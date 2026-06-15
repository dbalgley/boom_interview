"""Shared data models for the CFD workflow."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Union

DEFAULT_SOLVER_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class SimulationCase:
    """Input parameters for a single jet3D simulation case."""

    pressure: int
    temperature: float
    mach: float

    @property
    def case_name(self) -> str:
        """Stable case identifier used for input and output filenames."""
        return f"m{self.mach}_p{self.pressure}_t{self.temperature}"

    def input_path(self, case_dir: Path) -> Path:
        """Return the input file path for this case."""
        return case_dir / f"input_case_{self.case_name}.txt"

    def output_path(self, case_dir: Path) -> Path:
        """Return the output file path for this case."""
        return case_dir / f"result_case_{self.case_name}.log"


@dataclass(frozen=True)
class ForcesMoments:
    """Parsed force and moment values from a jet3D result file."""

    fx: float
    fy: float
    fz: float
    mx: float
    my: float
    mz: float


class SimulationStatus(str, Enum):
    """Execution status for a simulation case."""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INVALID_OUTPUT = "invalid_output"


@dataclass(frozen=True)
class SimulationResult:
    """Result metadata from attempting to run one simulation case."""

    case: SimulationCase
    status: SimulationStatus
    input_path: Path
    output_path: Path
    stdout: Union[bytes, str] = ""
    stderr: Union[bytes, str] = ""
    returncode: Union[int, None] = None
