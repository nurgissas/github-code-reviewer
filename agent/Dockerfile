FROM python:3.11-slim

WORKDIR /app

# System deps: libpq for postgres drivers, curl for the healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages first (better layer caching).
COPY agent/requirements.txt ./agent/requirements.txt
RUN pip install --no-cache-dir -r agent/requirements.txt

# Copy the agent package (keep it importable as `agent.*`).
COPY agent ./agent

EXPOSE 8000

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
