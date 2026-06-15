# jet3D Workflow

This project provides a maintainable command-line workflow around the `jet3D` CFD solver.

The original workflow generated solver inputs, executed `jet3D`, and post-processed result files from a single Python script. This refactor preserves that workflow while separating the code into smaller, testable modules for case IO, solver execution, orchestration, logging, and result parsing.

`jet3D` itself is treated as a black-box executable. The Python package does not modify or inspect solver internals; it calls the solver through a narrow adapter layer.

## What this tool does

The workflow supports three main operations:

* Run a single simulation case.
* Run a sweep of simulation cases from `input.dat`.
* Post-process a solver output file.

It also adds:

* Structured Python modules instead of one monolithic script.
* Unit tests around parsing, orchestration, solver handling, and CLI behavior.
* Bounded handling for solver errors and hangs.
* Captured stdout/stderr from the solver.
* A configurable solver path.
* A Docker image for reproducible execution.
* CI checks for tests, packaging, and Docker image builds.

## Repository layout

```text
.
├── bin/
│   └── jet3D
├── cases/
│   └── .keep
├── src/
│   ├── runner.py
│   └── cfd_pipeline/
│       ├── case_io.py
│       ├── cli.py
│       ├── logging_config.py
│       ├── models.py
│       ├── orchestrator.py
│       ├── postprocess.py
│       └── solver.py
├── tests/
├── input.dat
├── pyproject.toml
├── Dockerfile
├── NOTES.md
└── README.md
```

Important files:

* `src/runner.py` is the compatibility entrypoint matching the original commands.
* `bin/jet3D` is the provided CFD solver executable.
* `src/cfd_pipeline/solver.py` is the only module that directly invokes the solver process.
* `src/cfd_pipeline/orchestrator.py` coordinates case writing, solver execution, logging, and result handling.
* `src/cfd_pipeline/postprocess.py` parses solver output files.
* `NOTES.md` explains design decisions and future scaling ideas.

## Local setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the package in editable mode with development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Make sure the original executable entrypoints are executable:

```bash
chmod +x src/runner.py bin/jet3D
```

## Running locally

### Show CLI help

```bash
./src/runner.py --help
```

If installed, the package script can also be used:

```bash
jet3d-runner --help
```
> Note: The package script is installed via the above `python -m pip install -e ".[dev]" command`

### Run a single simulation

```bash
./src/runner.py --single --pressure 101325 --temperature 288.15 --mach 0.85
```

Equivalent installed command:

```bash
jet3d-runner --single --pressure 101325 --temperature 288.15 --mach 0.85
```

By default, outputs are written under `cases/`.

Example generated paths:

```text
cases/input_case_m0.85_p101325_t288.15.txt
cases/result_case_m0.85_p101325_t288.15.log
```

### Run a sweep

```bash
./src/runner.py --sweep ./input.dat
```

Equivalent installed command:

```bash
jet3d-runner --sweep ./input.dat
```

The sweep file is expected to contain rows with:

```text
pressure temperature mach
```

Malformed rows are skipped and logged.

### Progress display

Sweep runs show a progress bar when running in an interactive terminal:

```bash
./src/runner.py --sweep ./input.dat

### Post-process a result

```bash
./src/runner.py --postprocess result_case_m0.85_p101325_t288.15.log
```

The postprocess command looks for the file under the configured cases directory.

Equivalent explicit form:

```bash
./src/runner.py --dir ./cases --postprocess result_case_m0.85_p101325_t288.15.log
```

## Using a different solver executable locally

The included `bin/jet3D` is provided for the challenge and for reproducible local testing. The workflow does not require that exact path.

Use `--solver` to point at a different solver executable:

```bash
./src/runner.py \
  --single \
  --pressure 101325 \
  --temperature 288.15 \
  --mach 0.85 \
  --solver /path/to/another/jet3D
```

For a sweep:

```bash
./src/runner.py \
  --sweep ./input.dat \
  --solver /path/to/another/jet3D
```

The replacement solver should follow the same execution contract as the provided solver:

```text
solver_executable input_file output_file
```

The workflow expects the solver to write a result file containing a `Final Forces and Moments` line when successful.

## Running with Docker

The Docker image packages the Python workflow and the provided `bin/jet3D` executable so the project can be run without setting up a local Python environment.

Build the image locally:

```bash
python -m pip install --upgrade build
python -m build
docker build -t jet3d-workflow .
mkdir -p cases
sudo chown -R 13337:13337 cases
```
> Note: It is important that the bind-mount directory `cases/` is writable by the non-root numeric user 13337, which is the user running in the container.

Run help:

```bash
docker run --rm jet3d-workflow --help
```

Run a single case:

```bash
docker run --rm \
  -v "$PWD/cases:/app/cases" \
  jet3d-workflow \
  --single --pressure 101325 --temperature 288.15 --mach 0.85
```

Run a sweep:

```bash
docker run --rm \
  -v "$PWD/cases:/app/cases" \
  jet3d-workflow \
  --sweep ./input.dat
```

Post-process a result:

```bash
docker run --rm \
  -v "$PWD/cases:/app/cases" \
  jet3d-workflow \
  --postprocess result_case_m0.85_p101325_t288.15.log
```

The volume mount keeps generated case files and result logs on the host machine.

## Using a different solver executable with Docker

The Docker image includes the provided `bin/jet3D` for convenience, but a different solver can be mounted into the container and selected with `--solver`.

Example:

```bash
docker run --rm \
  -v "$PWD/cases:/app/cases" \
  -v "$PWD/my_solver/jet3D:/solver/jet3D:ro" \
  jet3d-workflow \
  --single --pressure 101325 --temperature 288.15 --mach 0.85 \
  --solver /solver/jet3D
```

For a sweep:

```bash
docker run --rm \
  -v "$PWD/cases:/app/cases" \
  -v "$PWD/my_solver/jet3D:/solver/jet3D:ro" \
  jet3d-workflow \
  --sweep ./input.dat \
  --solver /solver/jet3D
```

This allows the Python orchestration layer to remain stable while engineers test or deploy different solver builds.

## Docker Hub image

An image has been published to Docker Hub automatically via GitHub CD, pull it with:

```bash
docker pull davisb42/jet3d-workflow:latest
```

Then run:

```bash
docker run --rm \
  -v "$PWD/cases:/app/cases" \
  <dockerhub-username>/jet3d-workflow:latest \
  --single --pressure 101325 --temperature 288.15 --mach 0.85
```

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Run type checks:

```bash
mypy src tests
```

Run formatting and lint checks:

```bash
ruff format --check .
ruff check .
```

Run pre-commit checks:

```bash
pre-commit run --all-files
```

Build the Python package:

```bash
python -m build
```

Build the Docker image:

```bash
docker build -t jet3d-workflow .
```

Smoke-test the Docker image:

```bash
docker run --rm jet3d-workflow --help
```

## Contributing

When changing this project, prefer small changes that preserve the engineer-facing workflow.

General guidelines:

1. Keep `bin/jet3D` as a black box.

   * Do not modify the solver executable.
   * Route solver behavior changes through `solver.py` or CLI configuration.

2. Preserve the original command style where possible.

   * The original `./src/runner.py --single`, `--sweep`, and `--postprocess` workflows should continue to work.

3. Keep modules focused.

   * CLI parsing belongs in `cli.py`.
   * Case input/output logic belongs in `case_io.py`.
   * Solver subprocess handling belongs in `solver.py`.
   * Result parsing belongs in `postprocess.py`.
   * Workflow coordination belongs in `orchestrator.py`.

4. Test wrapper behavior without depending on solver randomness.

   * Unit tests should mock the solver process where possible.
   * The provided `jet3D` executable intentionally fails randomly, so tests should not rely on it for deterministic behavior.

5. Keep generated files out of version control.

   * Do not commit `__pycache__`, `*.egg-info`, `dist/`, `build/`, or generated case results.
   * The `cases/` directory should generally contain only `.keep`.

## Notes on scale

The current CLI preserves the original workflow and improves maintainability, but large sweeps of hundreds of thousands of cases need more than a serial command-line loop.

The next production step would be to add a durable case registry or manifest that tracks:

* Case inputs.
* Attempt count.
* Solver status.
* Failure reason.
* Input and output paths.
* Start and end timestamps.
* Retry eligibility.

From there, execution could move to parallel workers, a job queue, Kubernetes Jobs, AWS Batch, or an HPC scheduler. Postprocessed results should be written to a structured store such as CSV, Parquet, DuckDB, PostgreSQL, or another analysis-friendly backend so engineers can query and explore sweep results without manually inspecting output files.

See `NOTES.md` for more detail on design decisions and future system architecture.
