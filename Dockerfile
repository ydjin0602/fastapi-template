# Делаем свой базовый образ с установкой переменных окружения
FROM python:3.13.5-slim as base-image

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_HOME="/root/.local/bin" \
    UV_PROJECT_ENVIRONMENT="/app/.venv" \
    PROJECT_PATH="/app"

ENV PATH="$UV_HOME:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем пользователя и группу
RUN groupadd --gid 2000 user && useradd --uid 2000 --gid user --shell /bin/bash --create-home user

# Создаем рабочую директорию
RUN mkdir -p /app && chmod 777 /app
WORKDIR /app

# Устанавливаем Poetry
RUN pip install uv

# Копируем файлы проекта
COPY --chown=user:user pyproject.toml uv.lock ./

# Устанавливаем зависимости (без установки самого проекта)
RUN uv sync --frozen --no-install-project

##############################################################
# Образ для разработки
FROM base-image AS development-image
ENV COMMON__ENVIRONMENT=DEV

# Копируем код приложения
COPY --chown=user:user ./app /app/app
COPY --chown=user:user ./alembic.ini /app/
COPY --chown=user:user ./migrations /app/migrations

# Устанавливаем wait-for-it.sh (ждём Postgres перед миграциями)
RUN curl -o /usr/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/bin/wait-for-it.sh

USER user

CMD ["uv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "3000"]

##############################################################
# Образ для миграций Alembic
FROM development-image AS alembic-image
CMD ["sh", "-c", "uv run alembic -c ./alembic.ini -x data=true upgrade head && exit 0"]

##############################################################
# Образ для тестирования
FROM base-image AS test-image
ENV COMMON__ENVIRONMENT=PYTEST

COPY --chown=user:user ./app /app/app
COPY --chown=user:user ./alembic.ini /app/
COPY --chown=user:user ./migrations /app/migrations
COPY --chown=user:user ./tests /app/tests

USER user
CMD ["uv", "run", "pytest", "--cov=app", "-vv", "--cov-config", ".coveragerc", "--junitxml=report.xml"]

##############################################################
# Образ для production
FROM base-image AS production-image
ENV COMMON__ENVIRONMENT=PROD

COPY --chown=user:user ./app /app/app

USER user
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
