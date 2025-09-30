FROM python:3.13.5-alpine AS builder
LABEL maintainer="Tobias Goetz <contact@tobiasgoetz.com>"

RUN apk update
RUN apk add git

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /pibot-build

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable


COPY . .

RUN uv build --wheel

WORKDIR /pibot

RUN uv venv

# Install the wheel file inside the virtual environment
RUN uv pip install /pibot-build/dist/*.whl

FROM python:3.13.5-alpine AS runtime

WORKDIR /pibot

# Copy only the virtual environment from the builder stage
COPY --from=builder /pibot/.venv /pibot/.venv

ENV PYTHONUNBUFFERED=1
ENV PATH="/pibot/.venv/bin:$PATH"

CMD ["python", "-m", "pibot"]
