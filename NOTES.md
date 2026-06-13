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


### QUESTIONS ID ASK THE DEV
- Is the int on temperature intentional in casename?
- HOw long should Jet3D run for befor i should time it out?
