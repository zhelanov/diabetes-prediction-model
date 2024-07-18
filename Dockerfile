# syntax=docker/dockerfile:1
# Keep this syntax directive! It's used to enable Docker BuildKit
# Source: https://github.com/orgs/python-poetry/discussions/1879#discussioncomment-7284113

################################
# PYTHON-BASE
# Sets up all our shared environment variables
################################
FROM python:3.12.4-slim as python-base

# https://python-poetry.org/docs/configuration/#using-environment-variables
ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    VIRTUAL_ENV="/venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VIRTUAL_ENV/bin:$PATH"

# prepare virtual env
RUN python -m venv $VIRTUAL_ENV

# working directory and Python path
WORKDIR /app
ENV PYTHONPATH="/app:$PYTHONPATH"

################################
# BUILDER-BASE
# Used to build deps + create our virtual environment
################################
FROM python-base as builder-base
RUN apt-get update && \
    apt-get install -y \
    apt-transport-https \
    gnupg \
    ca-certificates \
    build-essential \
    git \
    curl

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
# The --mount will mount the buildx cache directory to where
# Poetry and Pip store their cache so that they can re-use it
RUN --mount=type=cache,target=/root/.cache \
    curl -sSL https://install.python-poetry.org | python -

# used to init dependencies
WORKDIR /app
COPY poetry.lock pyproject.toml ./
COPY scripts scripts/
COPY diabetes_prediction_model.py diabetes_prediction_model.py

# install runtime deps to VIRTUAL_ENV
RUN --mount=type=cache,target=/root/.cache \
    poetry install --no-root --only main

# build C dependencies. Remove if you don't need.
# RUN --mount=type=cache,target=/app/scripts/vendor \
#     poetry run python scripts/build-c-denpendencies.py && \
#     cp scripts/lib/*.so /usr/lib

################################
# DEVELOPMENT
# Image used during development / testing
################################
FROM builder-base as development

WORKDIR /app

# quicker install as runtime deps are already installed
RUN --mount=type=cache,target=/root/.cache \
    poetry install --no-root --with test,lint

EXPOSE 8080
CMD ["bash"]


################################
# PRODUCTION
# Final image used for runtime
################################
FROM python-base as production

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    apt-get clean

# copy in our built poetry + venv
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $VIRTUAL_ENV $VIRTUAL_ENV
# copy in our C dependencies. Remove if you don't need.
# COPY --from=builder-base /app/scripts/lib/*.so /usr/lib

WORKDIR /app
COPY poetry.lock pyproject.toml ./
COPY diabetes_prediction_model.py diabetes_prediction_model.py
COPY run_experiment.py run_experiment.py

EXPOSE 8080
ENTRYPOINT ["python", "run_experiment.py"]
