FROM python:3.11-slim AS base

# Create non-root user to run the app. Kubesec suggest a UID >10000 to avoid
# colliding with system users. USER and UID are args so it's more convenient
# to use in the Dockerfile. Overriding them is not necessary or recommended.
ARG UID=13337
ARG USER=runner
USER root

RUN useradd --uid "${UID}" --create-home --user-group "${USER}"

USER "${UID}:${UID}"

ENV VIRTUAL_ENV=/home/${USER}/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"


FROM base AS builder

USER root

RUN python -m venv "${VIRTUAL_ENV}" \
    && "${VIRTUAL_ENV}/bin/python" -m pip install --upgrade pip setuptools wheel \
    && chown -R "${USER}:${USER}" "${VIRTUAL_ENV}"

USER "${UID}:${UID}"

WORKDIR /home/${USER}

COPY --chown=${USER}:${USER} pyproject.toml pyproject.toml

# Runtime dependencies
RUN python -c 'import tomllib; f = open("pyproject.toml", "rb"); c = tomllib.load(f); f.close(); print("\n".join(c["project"]["dependencies"]))' \
    | pip install --no-cache-dir -r /dev/stdin


FROM base AS final

WORKDIR /app

USER root

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
    && rm -f /tmp/*.whl \
    && chown -R "${USER}:${USER}" "${VIRTUAL_ENV}"

COPY --chown=${USER}:${USER} bin ./bin
COPY --chown=${USER}:${USER} input.dat ./input.dat
COPY --chown=${USER}:${USER} src/runner.py ./src/runner.py

RUN chmod +x ./bin/jet3D ./src/runner.py \
    && mkdir -p /app/cases \
    && chown -R "${USER}:${USER}" /app

USER "${UID}:${UID}"

ENTRYPOINT ["./src/runner.py"]
