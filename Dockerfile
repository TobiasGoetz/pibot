FROM python:3.14-alpine AS builder
LABEL maintainer="Tobias Goetz <contact@tobiasgoetz.com>"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /pibot-build

# Copy only build inputs to avoid invalidating cache on unrelated changes
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv build --wheel

WORKDIR /pibot

RUN uv venv

# Install the built wheel file inside the virtual environment
RUN uv pip install /pibot-build/dist/*.whl

FROM python:3.14-alpine AS runtime

WORKDIR /pibot

# Copy only the virtual environment from the builder stage
COPY --from=builder /pibot/.venv /pibot/.venv

ENV PYTHONUNBUFFERED=1
ENV PATH="/pibot/.venv/bin:$PATH"

CMD ["pibot"]
