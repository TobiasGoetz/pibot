# Stage 1: Builder
FROM python:3.13.2-alpine as builder
LABEL maintainer="Tobias Goetz <contact@tobiasgoetz.com>"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /pibot

# Copy the built wheel file (make sure to have run `uv build` before)
COPY dist/*.whl .

# Create a virtual environment using uv
RUN uv venv

# Install the wheel file inside the virtual environment
RUN uv pip install *.whl

# Stage 2: Final Runtime Image
FROM python:3.13.2-alpine as runtime

# Set the working directory
WORKDIR /pibot

# Copy only the virtual environment from the builder stage
COPY --from=builder /pibot/.venv /pibot/.venv

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/pibot/.venv/bin:$PATH"

# Run the package with Python
CMD ["python", "-m", "pibot"]
