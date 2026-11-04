# План: актуализация fastapi-template по итогам анализа convpn-проектов

Дата: 2026-11-05
Источник: diff-анализ 6 проектов (`~/convpn/{users,tariffs,referrals,payment-gateway,remnawave-gateway,vpn-bot}`)
Решения пользователя: Redis — включить (с FIXME), Kafka/FastStream — включить (с FIXME), Python — 3.14.8 (последний), CSRF — оставить.

## Цели
1. Перенести улучшения, к которым пришли все проекты.
2. Обновить зависимости и Python до последних.
3. Починить нелучшие места шаблона.
4. Сохранить работоспособность: линтеры + тесты зелёные.

## Версии (проверены резолвом в /tmp/tpl-probe на CPython 3.14)

Runtime: `asyncpg==0.32.0`, `fastapi[all]==0.162.0`, `uvicorn[standard]==0.54.0`,
`sqlalchemy==2.1.8`, `alembic==1.20.1`, `orjson==3.13.0`, `loguru==0.7.3`,
`pydantic-settings==2.16.2`, `starlette-exporter==0.24.0`, `dishka==1.10.1`,
**новые**: `redis==8.1.0`, `faststream[confluent]==0.7.8`, `dishka-faststream==0.7.0`.

Dev: `testcontainers==4.15.0`, `asgi-lifespan==2.1.0`, `pytest==9.2.0`, `mypy==2.4.1`,
`pre-commit==4.7.0`, `pytest-asyncio==1.4.1.post1`, `pytest-alembic==0.13.2`,
`pytest-cov==7.1.0`, `ruff==0.17.3`, `schemathesis==4.33.1`.

pre-commit revs: hooks `v6.0.0` (без изм.), ruff `v0.17.3`, mypy `v2.4.1`.
Docker: `python:3.14.8-slim`, `ghcr.io/astral-sh/uv:0.13.1`.

---

## Task 1: pyproject.toml + pre-commit + lock

**Files:** `pyproject.toml`, `.pre-commit-config.yaml`, `uv.lock`

1. `requires-python = "==3.14.8"`; `version = "0.4.0"`.
2. Обновить пины deps/dev-групп до версий из раздела «Версии». Добавить redis/faststream/dishka-faststream.
3. `[tool.mypy] python_version = 3.14`; `[tool.ruff] target-version = "py314"`.
4. `.pre-commit-config.yaml`: ruff `v0.17.3`, mypy `v2.4.1` (+ types-python-dateutil оставить).
5. `uv lock` (свежий lock), `uv sync`.

Проверка: `uv lock --check` OK.

## Task 2: config.py — Redis + Kafka

**Files:** `app/config.py`, `env.example`

1. Добавить `RedisSettings` (host/port/username/password + `broker_url` property, как в convpn/users, без бизнес-TTL).
2. Добавить `KafkaSettings` (bootstrap_servers, consumer_group, enabled: bool = False — флаг вкл/выкл интеграции; при False lifespan не стартует брокер).
3. В `Settings`: `redis: RedisSettings = RedisSettings()`, `kafka: KafkaSettings = KafkaSettings()`.
4. FIXME-комментарии: «удали секцию/провайдеров, если Redis/Kafka не нужны».
5. `env.example`: добавить `REDIS__*`, `KAFKA__*`.

## Task 3: DI — Redis и KafkaBroker

**Files:** `app/api/di/application.py`, `app/api/di/request.py`

1. `ApplicationProvider`: `redis_pool_scope` (APP, ConnectionPool, decode_responses=True) — как в convpn/users.
2. `ApplicationProvider`: `kafka_broker_scope` (APP → KafkaBroker) с FIXME.
3. `RequestProvider`: `redis_scope` (REQUEST, `Redis(connection_pool=...)`) — как в convpn/vpn-bot.
4. FIXME-маркеры на каждом блоке.

## Task 4: main.py — FastStream lifecycle + CORS

**Files:** `app/main.py`

1. `_warmup_dependencies`: при `config.kafka.enabled` — взять KafkaBroker из DI, `FastStream(broker)`, `setup_dishka` (dishka_faststream, auto_inject=True),注册 подписчиков через `faststream_router(broker)`, `await app.start()`. Сохранить ссылку для stop.
2. В lifespan после `yield`: `await _shutdown_dependencies()` → stop faststream (в convpn/users stop отсутствует — чиним).
3. CORS: раскомментировать как в convpn/users (без allow_credentials), при заданном `backend_cors_origins`.
4. Пример консюмера: `app/api/v1/faststream_consumers/router.py` + закомментированный пример колбэка с FIXME.

## Task 5: base_crud — returning() и Any id

**Files:** `app/api/v1/crud/base_crud.py`

1. `create()`: `insert(...).returning(self.model)` + `scalars().first()` вместо повторного `get()` (из convpn/payment-gateway), но оставить типизированные ошибки шаблона (UniqueError/NotFoundError/DatabaseError).
2. `update()`: `_id: int` → `_id: Any` (UUID PK).
3. Проверить `delete()` на тот же паттерн.

## Task 6: utils-мелочи

**Files:**
- `app/api/utils/enums/base_enum.py`: типизация `Any` в `_missing_`/`values` + `to_dict()` (из vpn-bot)
- `app/api/utils/enums/env_enum.py`: добавить `STAGE = 'STAGE'`
- `app/api/utils/sqlalchemy/annotated_fields.py`: добавить `model_uuid` (server_default=func.gen_random_uuid()) рядом с FIXME про выбор PK
- `app/api/utils/health_check.py`: убрать `route_class=DishkaRoute` (там нет DI-зависимостей)

## Task 7: Dockerfile — multi-stage по паттерну проектов

**Files:** `Dockerfile`

Паттерн из convpn (uv_bin → builder → base → targets), но сохранить стадии dev/test/alembic, которые использует docker-compose шаблона:

- `uv_bin`: `ghcr.io/astral-sh/uv:0.13.1`
- `builder`: python:3.14.8-slim + gcc/build-essential, `uv sync --frozen --no-install-project --no-dev`, cache-mount, `UV_COMPILE_BYTECODE=1`
- `base-image`: python:3.14.8-slim, PATH=/app/.venv/bin, юзер 2000, chown вместо `chmod 777`, venv из builder
- `development-image`: FROM base + uv sync c dev-зависимостями (--with-dev поверх lock) + код/alembic/migrations → uvicorn --reload
- `alembic-image`: FROM development-image → `alembic -x data=true upgrade head`
- `test-image`: FROM development-image + tests → pytest
- `production-image`: FROM base + код → `CMD ["uvicorn", ...]` (напрямую, без `uv run`)
- Убрать: wait-for-it (compose healthcheck уже гарантирует готовность pg), curl из образа, 777.

Проверка: `docker build` всех таргетов.

## Task 8: docker-compose + env.example

**Files:** `docker-compose.yml`, `env.example`

1. Добавить `redis` (redis:8-alpine, healthcheck `redis-cli ping`, volume, profiles dev/db).
2. `template_service`/`alembic` depends_on redis (service_healthy).
3. env.example: REDIS__*, KAFKA__*.

## Task 9: Makefile

**Files:** `Makefile`, `Makefile.example` (удалить), README-упоминания

1. Префиксы `uv run` у всех python-таргетов (из convpn/tariffs).
2. `deps-up: docker compose --profile db up -d postgresql redis`.
3. Фикс: `test` использует `-m "not slow"` (маркер в pyproject — `slow`, а не `long`). `test_long` → `test_slow` с `-m slow`? Оставить test_long имя, поменять маркер — нет: переименовать в `test_slow`/`test` для консистентности.
4. Удалить `Makefile.example` (дубликат), проверить что README не ссылается.

## Task 10: README

**Files:** `README.md`

Обновить: версия Python 3.14.8, новые ENV (REDIS__*, KAFKA__*), make-таргеты (deps-up), стадии Dockerfile, упоминание FastStream-консюмеров и как выключить (KAFKA__ENABLED=false), Redis-провайдеры. Убрать упоминания Makefile.example, если есть.

## Task 11: Верификация

1. `uv sync && uv run pre-commit run --all-files` (ruff+mypy на новых версиях — чинить новые замечания).
2. `uv run pytest -m "not slow"` — базовые тесты без контейнеров.
3. `uv run pytest` (вкл. testcontainers-миграции; Docker доступен 29.6.1).
4. `docker build` основных таргетов.
5. Импорт app.main без Redis/Kafka (ленивые провайдеры не должны рваться при старте без брокера).

## Коммиты
Один коммит на Task (1–10), финальная верификация Task 11 перед последним коммитом.
