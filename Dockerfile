FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy dependency metadata first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install deps into /app/.venv
RUN uv sync --frozen --no-dev

# Copy project files
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Your app.py is in /app/api and imports `from settings import ...`
WORKDIR /app/api

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
