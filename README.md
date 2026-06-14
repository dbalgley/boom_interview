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

### Post-process a result

```bash
./src/runner.py --postprocess result_case_m0.85_p101325_t288.15.log
```

The postprocess command looks for the file under the configured cases directory.

Equivalent explicit form:

```bash
./src/runner.py --dir ./cases --postprocess result_case_m0.85_p101325_t288.15.log
```
