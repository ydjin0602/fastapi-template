# Пин версии uv для воспроизводимых сборок
FROM ghcr.io/astral-sh/uv:0.13.1 AS uv_bin
##############################################################
# СТАДИЯ 1: Builder (сборка прод-зависимостей)
##############################################################
FROM python:3.14.8-slim AS builder
COPY --from=uv_bin /uv /uvx /bin/
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT="/app/.venv"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev
##############################################################
# СТАДИЯ 1.1: Builder для разработки (прод + dev-зависимости)
##############################################################
FROM builder AS builder-dev
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project
##############################################################
# СТАДИЯ 2: Base Runtime (общий фундамент, без компиляторов)
##############################################################
FROM python:3.14.8-slim AS base-image
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"
RUN groupadd --gid 2000 user && \
    useradd --uid 2000 --gid user --shell /bin/bash --create-home user && \
    mkdir /app && chown user:user /app
WORKDIR /app
COPY --from=builder --chown=user:user /app/.venv /app/.venv
##############################################################
# Образ для разработки
##############################################################
FROM base-image AS development-image
ENV COMMON__ENVIRONMENT=DEV
COPY --from=builder-dev --chown=user:user /app/.venv /app/.venv
COPY --chown=user:user ./app /app/app
COPY --chown=user:user ./alembic.ini /app/
COPY --chown=user:user ./migrations /app/migrations
USER user
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "3000"]
##############################################################
# Образ для миграций Alembic
# (готовность Postgres гарантирует healthcheck в docker-compose)
##############################################################
FROM development-image AS alembic-image
CMD ["sh", "-c", "alembic -c ./alembic.ini -x data=true upgrade head && exit 0"]
##############################################################
# Образ для тестирования
##############################################################
FROM development-image AS test-image
ENV COMMON__ENVIRONMENT=PYTEST
COPY --chown=user:user ./tests /app/tests
COPY --chown=user:user .coveragerc /app/
USER user
CMD ["pytest", "--cov=app", "-vv", "--cov-config", ".coveragerc", "--junitxml=report.xml"]
##############################################################
# Образ для production
##############################################################
FROM base-image AS production-image
ENV COMMON__ENVIRONMENT=PROD
COPY --chown=user:user ./app /app/app
USER user
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
