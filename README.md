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

Create and activate a virtual environment.

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

On Linux, macOS, or WSL:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the package in editable mode with development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Linux, macOS, or WSL, ensure the original executable entrypoints are executable:

```bash
chmod +x src/runner.py bin/jet3D
```

Windows users running through `python .\src\runner.py` or the installed `cfd-pipeline` command do not need the `chmod` step.

## Running locally

### Show CLI help

On Windows PowerShell, prefer the installed command:

```powershell
cfd-pipeline --help
```

Or run the compatibility entrypoint through Python:

```powershell
python .\src\runner.py --help
```

On Linux, macOS, or WSL:

```bash
./src/runner.py --help
```

If installed, the package script can also be used:

```bash
cfd-pipeline --help
```

> Note: The package script is installed via the above `python -m pip install -e ".[dev]"` command.

### Run a single simulation

On Windows PowerShell:

```powershell
cfd-pipeline --single --pressure 101325 --temperature 288.15 --mach 0.85
```

Or:

```powershell
python .\src\runner.py --single --pressure 101325 --temperature 288.15 --mach 0.85
```

On Linux, macOS, or WSL:

```bash
./src/runner.py --single --pressure 101325 --temperature 288.15 --mach 0.85
```

Equivalent installed command:

```bash
cfd-pipeline --single --pressure 101325 --temperature 288.15 --mach 0.85
```

By default, outputs are written under `cases/`.

Example generated paths:

```text
cases/input_case_m0.85_p101325_t288.15.txt
cases/result_case_m0.85_p101325_t288.15.log
```

### Run a sweep

On Windows PowerShell:

```powershell
cfd-pipeline --sweep .\input.dat
```

Or:

```powershell
python .\src\runner.py --sweep .\input.dat
```

On Linux, macOS, or WSL:

```bash
./src/runner.py --sweep ./input.dat
```

Equivalent installed command:

```bash
cfd-pipeline --sweep ./input.dat
```

The sweep file is expected to contain rows with:

```text
pressure temperature mach
```

Malformed rows are skipped and logged.

### Progress display

Sweep runs show a progress bar when running in an interactive terminal.

On Windows PowerShell:

```powershell
cfd-pipeline --sweep .\input.dat
```

On Linux, macOS, or WSL:

```bash
./src/runner.py --sweep ./input.dat
```

To disable the progress display:

```powershell
cfd-pipeline --sweep .\input.dat --no-progress
```

### Post-process a result

On Windows PowerShell:

```powershell
cfd-pipeline --postprocess result_case_m0.85_p101325_t288.15.log
```

Or:

```powershell
python .\src\runner.py --postprocess result_case_m0.85_p101325_t288.15.log
```

The postprocess command looks for the file under the configured cases directory.

Equivalent explicit form on Windows PowerShell:

```powershell
cfd-pipeline --dir .\cases --postprocess result_case_m0.85_p101325_t288.15.log
```

On Linux, macOS, or WSL:

```bash
./src/runner.py --postprocess result_case_m0.85_p101325_t288.15.log
./src/runner.py --dir ./cases --postprocess result_case_m0.85_p101325_t288.15.log
```

## Using a different solver executable locally

The included `bin/jet3D` is provided for the challenge and for reproducible local testing. The workflow does not require that exact path.

Use `--solver` to point at a different solver executable.

On Windows PowerShell:

```powershell
cfd-pipeline `
  --single `
  --pressure 101325 `
  --temperature 288.15 `
  --mach 0.85 `
  --solver C:\path\to\another\jet3D.exe
```

For a sweep on Windows PowerShell:

```powershell
cfd-pipeline `
  --sweep .\input.dat `
  --solver C:\path\to\another\jet3D.exe
```

On Linux, macOS, or WSL:

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

> Note: The provided `bin/jet3D` executable may not run natively on Windows depending on how it was built. If it does not execute from PowerShell, use the Docker image or run the project from WSL.

## Running with Docker

The Docker image packages the Python workflow and the provided `bin/jet3D` executable so the project can be run without setting up a local Python environment.

Build the image locally:

```powershell
python -m pip install --upgrade build
python -m build
docker build -t cfd-pipeline .
mkdir cases
```

On Linux, macOS, or WSL:

```bash
python -m pip install --upgrade build
python -m build
docker build -t cfd-pipeline .
mkdir -p cases
```

Run help:

```powershell
docker run --rm cfd-pipeline --help
```

Run a single case on Windows PowerShell:

```powershell
docker run --rm `
  -v "${PWD}\cases:/app/cases" `
  cfd-pipeline `
  --single --pressure 101325 --temperature 288.15 --mach 0.85
```

Run a sweep on Windows PowerShell:

```powershell
docker run --rm `
  -v "${PWD}\cases:/app/cases" `
  -v "${PWD}\input.dat:/app/input.dat" `
  cfd-pipeline `
  --sweep /app/input.dat
```

Post-process a result on Windows PowerShell:

```powershell
docker run --rm `
  -v "${PWD}\cases:/app/cases" `
  cfd-pipeline `
  --postprocess result_case_m0.85_p101325_t288.15.log
```

The volume mount keeps generated case files and result logs on the host machine.

On Linux, macOS, or WSL, `chown` the cases/dir to the numeric 13337 user.

## Using a different solver executable with Docker

The Docker image includes the provided `bin/jet3D` for convenience, but a different solver can be mounted into the container and selected with `--solver`.

On Windows PowerShell:

```powershell
docker run --rm `
  -v "${PWD}\cases:/app/cases" `
  -v "${PWD}\my_solver\jet3D:/solver/jet3D:ro" `
  cfd-pipeline `
  --single --pressure 101325 --temperature 288.15 --mach 0.85 `
  --solver /solver/jet3D
```

For a sweep on Windows PowerShell:

```powershell
docker run --rm `
  -v "${PWD}\cases:/app/cases" `
  -v "${PWD}\input.dat:/app/input.dat:ro" `
  -v "${PWD}\my_solver\jet3D:/solver/jet3D:ro" `
  cfd-pipeline `
  --sweep /app/input.dat `
  --solver /solver/jet3D
```

On Linux, macOS, or WSL:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/cases:/app/cases" \
  -v "$PWD/my_solver/jet3D:/solver/jet3D:ro" \
  cfd-pipeline \
  --single --pressure 101325 --temperature 288.15 --mach 0.85 \
  --solver /solver/jet3D
```

For a sweep:

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/cases:/app/cases" \
  -v "${PWD}\input.dat:/app/input.dat:ro" \
  -v "$PWD/my_solver/jet3D:/solver/jet3D:ro" \
  cfd-pipeline \
  --sweep /app/input.dat \
  --solver /solver/jet3D
```

This allows the Python orchestration layer to remain stable while engineers test or deploy different solver builds.

## Docker Hub image

An image has been published to Docker Hub automatically via GitHub CD. Pull it with:

```powershell
docker pull davisb42/cfd-pipeline:latest
```

Then run on Windows PowerShell:

```powershell
mkdir cases

docker run --rm `
  -v "${PWD}\cases:/app/cases" `
  davisb42/cfd-pipeline:latest `
  --single --pressure 101325 --temperature 288.15 --mach 0.85
```

On Linux, macOS, or WSL:

```bash
mkdir -p cases

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/cases:/app/cases" \
  davisb42/cfd-pipeline:latest \
  --single --pressure 101325 --temperature 288.15 --mach 0.85
```

## Development

Install development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run the test suite:

```powershell
pytest
```

Run type checks:

```powershell
mypy src tests
```

Run formatting and lint checks:

```powershell
ruff format --check .
ruff check .
```

Run pre-commit checks:

```powershell
pre-commit run --all-files
```

Build the Python package:

```powershell
python -m build
```

Build the Docker image:

```powershell
docker build -t cfd-pipeline .
```

Smoke-test the Docker image:

```powershell
docker run --rm cfd-pipeline --help
```

The same commands also work on Linux, macOS, and WSL.

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
