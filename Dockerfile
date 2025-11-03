FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

# + netcat para health/wait e gosu para drop de privilégios
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
     build-essential \
     python3-dev \
     libpq-dev \
     libjpeg-dev \
     zlib1g-dev \
     libssl-dev \
     libffi-dev \
     pkg-config \
     rustc \
     cargo \
     curl \
     netcat-openbsd \
     gosu \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --group dev

COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]