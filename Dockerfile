FROM python:v3.12 as base

# Create non-root user to run the app. Kubesec suggest a UID >10000 to avoid
# colliding with system users. USER and UID are args so it's more convenient
# to use in the Dockerfile. Overriding them is not necessary or recommended.
ARG UID=13337
ARG USER=runner
USER root
RUN useradd --uid ${UID} -Um ${USER}
USER ${UID}:${UID}

# Setup venv variables
ENV VIRTUAL_ENV=/home/${USER}/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


# Use this stage to build the dependency venv. Sometimes this requires special devel
# packages (gcc, python-devel, etc.) so install those here. They will not get copied to
# the final image.
FROM base as builder

# Upgrade Python build/install tooling
RUN pip install --upgrade pip setuptools

# Setup the virutalenv
RUN python3 -m venv $VIRTUAL_ENV

# Pre install dependencies for layer optimization
WORKDIR /home/${USER}
COPY --chown=${USER}:${USER} pyproject.toml pyproject.toml
RUN python -c 'import tomllib; f = open("pyproject.toml", "rb"); c = tomllib.load(f); f.close(); print("\n".join(c["project"]["dependencies"]))' | pip install -r /dev/stdin


# This is the final runtime image. It only includes packages needed to run the app
FROM base as final

# Copy in the final venv
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Install the app wheel. Using mount prevents an extra copy of the wheel living in the
# docker image layers. This also doesn't cache well, so having it last is ideal.
RUN --mount=type=bind,target=/data/dist,source=dist/ \
   pip install --no-cache-dir /data/dist/example_project*.whl

ENTRYPOINT [ "example-project" ]
