FROM python:3.13.2-alpine
LABEL maintainer="Tobias Goetz <contact@tobiasgoetz.com>"

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /pibot

# Copy the project into the image
COPY . /pibot

# Install the project
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_PIBOT=0.1.0
RUN uv sync --frozen

# Set environment variables
#make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "pibot"]
