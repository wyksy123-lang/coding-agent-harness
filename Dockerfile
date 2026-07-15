FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY pyproject.toml ./
COPY harness ./harness
COPY webui ./webui
COPY demo ./demo

RUN python -m pip install --upgrade pip build \
    && python -m build --wheel

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY --from=builder /build/dist/*.whl /tmp/

RUN python -m pip install --upgrade pip \
    && python -m pip install /tmp/*.whl \
    && rm -rf /tmp/*.whl /root/.cache/pip

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn webui.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
