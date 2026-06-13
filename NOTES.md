# NOTES

Use this file to explain how you approached the challenge.

We’re especially interested in:
- Why you structured and cleaned up the code the way you did
- What design decisions or tradeoffs you made
- Any larger systems (e.g. orchestration, batch execution, storage) you considered but didn’t implement
- How you’d scale or integrate this into a broader workflow

You don’t need to write a novel — just enough to show us how you think.

###########################

- Discuss files as system of record, definitely not the most effective
    - Case Registry in RDB (PostgreSQL), track definitions, execution state, retries, times, output loc, result metadata
- "Postprocessing is not set up to allow an engineer to explore large set of results efficiently"
    - Came up during interview 2x (I think)
    - "How does an engineer learn something from 300,000 runs?""
        - Outputs in structured form
        - Parquet (???)
        - RDB/"DuckDB"
        For log files
    - Enabling filtering, sorting, aggregation, plotting, dashboarding to "increase time-to-insight"
- Discuss "Added automated formatting, linting, and type-checking via pre-commit hooks to improve consistency and catch common issues before changes are committed."

Case Generator -> Case Registry (DB) -> Worker Pool (with retry/backoff) -> Result Store (Parquet/DuckDB) -> Analytics Layer -> (Jupyter/Dashboard/API)

- Think about *SEPARATING* solver orchestration from solver execution. CFD tools are usually 3rd party tools. Treat is as a black box and define a clear execution interface, so orchestration layer can remain stable even if the sovler changes

1. Refactor for readability
2. Introduce tests
3. Fault tolerance and retries
4. Execution tracking
5. Concurrency
6. Discuss large-scale arch in NOTES
7. Discuss analysis/data-discovery workflow in NOTES

ADD:
- Pytest
- mypy
- ruff
- type hints
    - Defend, Gus and I talked at length about this (weakly typed languages with type hints is a half measure)
- dataclasses or *pydantic models*
- logging
- dockerfile
- github actions

###
cli.py # argparse only models.py # SimulationCase, SimulationResult, ForcesMoments case_io.py # write input files, read sweep files solver.py # calls ./bin/jet3D postprocess.py # parses result logs runner.py # orchestration glue

Working notes:
- runner.py has: cli parsing, case generation, solver execution, sweep parsing, and postprocessing all mixed
- single and sweep execution duplicate most of the same logic
- error handling is too broad
- case naming is 9inconsistent (single "t288.15", sweep "t288")
- doesn't produce *structured* status
-I preserved the original command-line interface while moving the implementation into a package structure to improve maintainability and testability.
- Went with python 3.10, but will use a dockerfile for reproducable runtime. I would confirm engineering python constraints before making such a change however.
- dataclass instead of pydantic because we're not putting in an api endpoint (yet), or cloud queue.
- I intentionally kept case parameter validation limited to parsing and type conversion rather than imposing physics-domain constraints. In a real CFD workflow, valid ranges should come from the engineering team or solver documentation rather than being inferred in the orchestration layer.
- replaced ad hoc print statements with logging framework, allowing for verbosity control, redirection, and batch/monitoring
- I forward solver stdout/stderr through dedicated loggers without rewriting the solver’s messages. This preserves the black-box solver output exactly while still making stream origin visible to the orchestration layer.
- audit trail or list of runs? append only exe manifest.
- I standardized case naming between single and sweep runs. The original script used full temperature precision for single cases but truncated temperature in sweep mode. I chose the full value in both modes to avoid filename collisions between cases such as 288.1 and 288.9. I did not alter the simulation inputs.

### QUESTIONS ID ASK THE DEV
- Is the int on temperature intentional in casename?
- HOw long should Jet3D run for befor i should time it out?
