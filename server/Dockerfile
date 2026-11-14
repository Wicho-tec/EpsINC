# Multi-stage Dockerfile for EpsInc Game Server
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Image
FROM python:3.10-slim AS runner

WORKDIR /app

# Create unprivileged application user
RUN groupadd -g 1000 epsinc && \
    useradd -u 1000 -g epsinc -s /bin/bash -m epsinc

COPY --from=builder /root/.local /home/epsinc/.local
ENV PATH=/home/epsinc/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy game code and static assets
COPY --chown=epsinc:epsinc server/ /app/server/
COPY --chown=epsinc:epsinc client/ /app/client/
COPY --chown=epsinc:epsinc run_game.py /app/run_game.py

USER epsinc

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
