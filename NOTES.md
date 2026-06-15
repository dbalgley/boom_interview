# NOTES

## Summary

My goal was to preserve the intent and usability of the original script while breaking the implementation into smaller, testable modules. The original `./src/runner.py` entrypoint remains available, and the existing `--single`, `--sweep`, and `--postprocess` workflows are still supported.

The refactor separates the original script into focused components for CLI parsing, case input/output, solver execution, orchestration, logging, and result parsing. I also added tests, type checking, linting/formatting, CI, and containerized execution to make the workflow easier to maintain and safer to extend.

The main goals were to make the workflow easier to understand, easier to test, and better prepared for larger CFD sweeps.

## Scope

I treated this as a bounded refactor rather than a full production rewrite. The goal was to improve structure, testability, and failure handling while preserving the original workflow. Larger system changes, such as distributed execution, retry orchestration, and structured result storage, are discussed as future work rather than implemented here.

## Refactor Approach

- Moved argument parsing into `cli.py`.
    - Added an optional `--solver` argument so a different CFD solver executable can be selected without changing the code.
- Added explicit models for simulation cases, solver results, statuses, and forces/moments.
- Moved case file generation and sweep file parsing into `case_io.py`.
- Moved solver subprocess handling into `solver.py`.
- Moved result parsing and validation into `postprocess.py`.
- Kept workflow coordination in `orchestrator.py`.
- Preserved `src/runner.py` as a compatibility wrapper for the original command style.
- Added logging to replace ad hoc `print` statements, but kept log messages and format as close to original as possible for compatibility.
- Added unit testing around parsing, CLI routing, solver behavior, orchestration, and postprocessing.
- Added packaging, Docker support, pre-commit hooks, and CI checks, publishing the artifact to DockerHub.
- Added optional status bar `tqdm` for UX.

## Key Design Decisions
### Preserving the engineer's workflow

I intentionally left the original CLI intact. The engineer can still run the commands they ran before, just as they ran them:
```shell
./src/runner.py --single --pressure 101325 --temperature 288.15 --mach 0.85
./src/runner.py --sweep ./input.dat
./src/runner.py --postprocess result_case_m0.85_p101325_t288.15.log
```
But they can also install the package and run it from a more compact command:
```bash
python -m pip install --upgrade pip
python -m pip install -e "."
cfd-pipeline --single --pressure 101325 --temperature 288.15 --mach 0.85
cfd-pipeline --sweep ./input.dat
cfd-pipeline --postprocess result_case_m0.85_p101325_t288.15.log
```
The implementation changed, but the basic user workflow did not.

### Treating `jet3D` as a Black Box

I did not modify `bin/jet3D`. I treated it as an external solver executable behind a small adapter layer in `solver.py`. The orchestration layer is responsible for creating input files, invoking the solver, capturing stdout/stderr, enforcing timeouts, and validating the output artifact. This keeps the Python workflow independent of solver internals and makes it easier to replace or relocate the solver later.

### Engineering Assumptions

I kept case validation focused on parsing and type conversion. I did not add physics-domain constraints such as valid pressure, temperature, or Mach ranges because I would have been making assumptions and such constraints should come from the engineering team or solver documentation rather than being inferred in the orchestration layer.

### Failure Handling

The solver can fail in several ways. The refactor distinguishes between process success and simulation success. A solver process can return successfully while still producing an unusable result file. Because output truncation is one of the stated failure modes, the runner validates successful process executions by checking that the output file contains a parseable `Final Forces and Moments` record, as defined in the data contract.

> Note: This design decision was a bit of a sticking point for me. The solution involves actually opening the resulting `*log` file that is generated from jet3D in order to validate, which may pose concerns when scaling up. I accepted this risk given the current conditions, but would investigate the time cost as the runs scaled up. I considered reading the stdout to determine the validity of the file, and also checking the files after the run. Both of these had a smell for various reasons.

The workflow now captures:
- solver stdout
- solver stderr
- return code
- timeout status
- invalid output status

Solver stdout and stderr are forwarded through dedicated loggers without rewriting the solver messages. This keeps the black box solver output visible while making the source of each log line clear.

> Note: Another small sticking point here. This results in a message like `2026-06-14 20:00:38,863 INFO [solver.stdout] [solver] success: ...` where the [...] shows up twice. I accepted this small design hiccup as I felt it was good to report the source of all the logs, and the binary itself reported status this way. I did not want to strip off the binary's "[solver]".

### Testing and Tooling Strategy

The test suite avoids depending on the real `jet3D` executable for various reasons, including its unpredictability. Instead, tests mock subprocess behavior and focus on deterministic wrapper logic.

The tests achieve 92% source coverage over such areas as:
- case name and path generation
- sweep file parsing
- case input writing
- solver success, nonzero exits, timeouts, OS errors, and invalid-output cases
- result parsing
- CLI routing
- sweep behavior after failures

I also added development tooling to make future changes safer and more consistent:
- pytest
- mypy, ruff, pre-commit
- GitHub Actions for CI
- package build checks
- Docker image build checks

### Docker and CI

I added a Dockerfile so the workflow can be run in a reproducible environment without requiring the engineer or reviewer to manage a local Python installation.

The Docker image includes the provided `bin/jet3D` executable for convenience, but the application does not require that exact binary. A different solver can be mounted into the container and selected with `--solver`.

> Note: For this exercise, I included the provided solver binary in the image so the workflow can be run end-to-end by a reviewer. In a production setting, I would confirm whether that is appropriate. A real CFD solver may be large, licensed, platform-specific, or better deployed separately from the orchestration layer.

This keeps the orchestration layer stable while allowing the solver binary to vary.

### Standardizing Naming

The original script differed slightly on how it named case files between single and sweep. Sweep truncated the temperature in the case file. I standardized on the full value to reduce the chance of filename collisions while leaving the actual simulation inputs unchanged. However, I would have asked the engineering team to confirm this behavior, and determine if it was intentional.

## Scaling to 300,000 Cases

The current implementation is still a local, serial command line workflow. This preserves the original usage pattern, but is not enough for hundreds of thousands of cases.

In my "report to the PM" about future work, the first item would be to introduce a case manifest that tracks things such as:
- case definition
- execution status
- attempt count
- retry eligibility
- start and end time
- input/output path
- failure reason
- parsed result metadata (maybe)
Along with retries/backoff. I feel that reporting the results to the engineering team in a way that is more than a pile of files or a terminal log is very important when you scale up.

Next, I would introduce a worker pool, case file checking and parallelization. I assume for the purposes of this future work that the results do not depend on one another and the caseload can be split amongst several workers. This would cut down on runtimes drastically. It would also be important as we scale to make sure the input, with its 300000 cases, actually achieves what the engineering team intends for it.

After that I would want to begin work on a result store to facilitate filtering, sorting, aggregation, plotting and comparison. Depending on the tools available, there are several avenues to investigate such as Parquet, DuckDB, or PostgreSQL.

Lastly, a GUI/Analytics layer would be implemented. This would be done with close collaboration of the engineering team to ensure they get a tool that is useful to them. Nothing would be worse than spending all this time on something they don't like using. Investigating things such as "what parameter regions produced interesting results?" or "which failures are retryable?". This would be how an engineer can explore 300,000 results without resorting to opening individual files.

## Open Questions

There are a few things I would confirm with the engineering team during my work on this:

- What are the valid input ranges for pressure, temperature, and Mach?
- Was the original sweep-mode temperature truncation in the case name intentional?
- What timeout is appropriate for a real jet3D run?
- Are solver stdout/stderr formats part of a stable contract, or are output files the only reliable result artifact?
- Should failed and invalid-output cases be retried automatically?
- What result format would best support the engineering analysis workflow?
