# Делаем свой базовый образ с установкой переменных окружения
FROM python:3.13.5-slim as base-image

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.2.1 \
    PROJECT_PATH="/app"

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Создаем пользователя и группу
RUN groupadd --gid 2000 user && useradd --uid 2000 --gid user --shell /bin/bash --create-home user

# Создаем рабочую директорию
RUN mkdir -p /app && chmod 777 /app
WORKDIR /app

# Устанавливаем Poetry
RUN pip install poetry

# Копируем файлы проекта
COPY --chown=user:user pyproject.toml poetry.lock ./

# Устанавливаем зависимости (без установки самого проекта)
RUN poetry install --no-root

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

CMD ["poetry", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "3000"]

##############################################################
# Образ для миграций Alembic
FROM development-image AS alembic-image
CMD ["sh", "-c", "poetry run alembic -c ./alembic.ini -x data=true upgrade head && exit 0"]

##############################################################
# Образ для тестирования
FROM base-image AS test-image
ENV COMMON__ENVIRONMENT=PYTEST

COPY --chown=user:user ./app /app/app
COPY --chown=user:user ./alembic.ini /app/
COPY --chown=user:user ./migrations /app/migrations
COPY --chown=user:user ./tests /app/tests

USER user
CMD ["poetry", "run", "pytest", "--cov=app", "-vv", "--cov-config", ".coveragerc", "--junitxml=report.xml"]

##############################################################
# Образ для production
FROM base-image AS production-image
ENV COMMON__ENVIRONMENT=PROD

COPY --chown=user:user ./app /app/app

USER user
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
