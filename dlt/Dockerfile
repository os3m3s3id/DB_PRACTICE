FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/


COPY dlt/requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY dlt/dlt_loading.py .
COPY data/ ./data/
ENV DATA_DIR=/app/data

ENTRYPOINT ["python", "dlt_loading.py"]