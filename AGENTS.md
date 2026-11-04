# AGENTS.md — fastapi-template

Инструкция для ИИ-агентов, работающих с проектами на базе этого шаблона
(FastAPI + SQLAlchemy 2.1 async + dishka + alembic + uv).

## Быстрые команды

```bash
uv sync                      # установка зависимостей (uv, Python запинен ==3.14.8)
make deps-up                 # поднять PG + Redis (docker compose, profile db)
make run                     # uvicorn на 127.0.0.1:8000 (локально; в докере порт 3000)
make test                    # pytest без slow-тестов (миграции пропускаются)
make test_slow               # все тесты, включая миграционные (нужен запущенный Docker)
make lint                    # pre-commit: ruff format + ruff check + mypy
make migrations_init         # первая миграция
make makemigrations MSG="..."  # автогенерация миграции
make migrate_with_data       # накат с data_upgrades()
make downgrade               # откат на 1 версию
```

Docker: `docker compose --profile dev up` (сервис + PG + Redis + миграции),
`--profile db` (только БД), `--profile app` (только сервис). Стадии образа:
`development-image`, `alembic-image`, `test-image`, `production-image`.

## Архитектура

Поток запроса: `router → controller → usecase → crud → model`.

```
app/
├── main.py                  # сборка приложения, lifespan (FastStream, CORS, prometheus)
├── config.py                # pydantic-settings; вложенность через "__" (COMMON__*)
├── api/
│   ├── di/                  # dishka-провайдеры (+ DI_CONTAINER)
│   │   ├── application.py   # APP: pg engine (AUTOCOMMIT), redis pool, kafka broker
│   │   ├── request.py       # REQUEST: AsyncSession, redis-клиент
│   │   └── usecase.py       # REQUEST: все юзкейсы — регистрируй новые здесь
│   ├── router.py            # корневой роутер
│   ├── utils/               # общие утилиты: ошибки, security, логгеры, sqlalchemy-типы
│   └── v1/
│       ├── controllers/     # только HTTP-слой: валидация + вызов ОДНОГО юзкейса
│       ├── usecases/        # бизнес-логика; FromDishka-зависимости
│       ├── crud/            # BaseCRUD[ModelT] + круды сущностей
│       ├── models/          # SQLAlchemy-модели (наследуют BaseDBModel)
│       ├── schemas/         # pydantic-схемы (наследуют BaseSchema)
│       └── faststream_consumers/  # Kafka-консюмеры (опционально, см. ниже)
migrations/                  # alembic; модели регистрируются в enabled_migration_models.py
tests/                       # фикстуры в conftest.py; см. раздел «Тесты»
```

## Ключевые правила

### Зависимости
- Всё через `uv` (`uv run`, `uv add`, `uv lock --check`).
- Пины точные (`pkg==x.y.z`) — так и оставляй. `greenlet` обязателен явно
  (sqlalchemy 2.1 async сам его не тянет).
- Версии ruff/mypy в `pyproject.toml` и в `.pre-commit-config.yaml` (rev) должны
  совпадать — бампай вместе.

### Конфигурация
- Только через env / `.env` (пример — `env.example`). Вложенность: `POSTGRES__HOST`.
- Переменная окружения обязательна одна: `COMMON__ENVIRONMENT`
  (`LOCAL|DEV|TEST|STAGE|PROD|PYTEST`). Не `ENVIRONMENT` — это ловушка.
- `.env` в git не попадает (gitignored) — новые переменные добавляй в `env.example`.

### Контроллеры и схемы
- В контроллере не должно быть логики — только вызов юзкейса `FromDishka`.
- У каждого эндпоинта обязателены `name`, `description` — их проверяет тест
  `test_swagger_docs.py`.
- Ошибки документируй через `get_responses(include_statuses=[...])`:
  400 (невалидное тело), 404 (нет записи/FK), 409 (уникальность), 422 (валидация).
- Идентификаторы в path — только `IdPath` из `base_schema.py` (int32-границы,
  иначе id > 2^31−1 даёт 500 из asyncpg).
- Числа в body, попадающие в PG `Integer`, ограничивай `Field(ge=1, le=2_147_483_647)`.
- Строки, попадающие в PG, ограничивай `Field(pattern=r'^[^\x00-\x1f]*$')` —
  NUL/контрол-символы дают 500 из VARCHAR.
- Ограничения request-схемы должны совпадать с response-схемой: если create
  пускает 1 символ, а response-модель требует 6 — запись сохранится, а ответ
  упадёт 500.

### Ошибки
- Единый формат ответа: `{"message": str, "code": InternalErrorEnum}`.
- Бизнес-ошибки — наследники `BaseError` (см. `utils/exceptions.py`), глобальный
  обработчик превратит их в нужный статус.
- `ORJSONResponse` в FastAPI 0.162+ deprecated — не использовать; сериализация
  через `response_model`, в хендлерах — `JSONResponse` + `jsonable_encoder`.

### БД и миграции
- Движок создаётся с `isolation_level='AUTOCOMMIT'`; транзакции управляются
  в юзкейсах (`_TransactionalMixin` оборачивает вызов, если у юзкейса есть
  `session`).
- Новая модель: создай в `app/api/v1/models/`, зарегистрируй в
  `migrations/enabled_migration_models.py`, схему добавь в `enabled_pg_schemas`
  в `migrations/env.py` (и в `__table_args__` модели). Схема по умолчанию
  `template_schema` — переименуй под проект.
- Сид-данные — в `data_upgrades()` миграции, накат через `make migrate_with_data`.

### Redis / Kafka (опциональные)
- Помечены `FIXME`-цепочками (config ↔ di ↔ main ↔ pyproject ↔ compose ↔
  env.example ↔ README): чтобы выкинуть, иди по ним.
- Kafka включается `KAFKA__ENABLED=true`; консюмеры — в
  `app/api/v1/faststream_consumers/` (пример в `example_callback.py`, подписка —
  в `router.py`). Интеграция DI — пакет `dishka-faststream` (встроенная в dishka
  — deprecated и не поддерживает faststream 0.7).
- Kafka в docker-compose НЕ включена (прод — helm): для локального запуска с
  консюмерами подними брокер руками.
- Redis-провайдеры ленивые: без обращений к `Redis` соединения не создаются.

### Стиль кода
- Ruff: одинарные кавычки, isort `force-single-line`, длина 88, google-docstrings.
- `except A, B:` без скобок допустим (PEP 758, Python 3.14+).
- Комментарии/докстринги — на русском, как в остальном коде.

## Тесты

- `pytest-asyncio`, `asyncio_mode=auto`, **loop scope = session** (конфиг в
  pyproject). Не создавай asyncpg-движки/сессии вне текущего loop — asyncpg
  привязывает соединение к loop'у создания («attached to a different loop»).
- PG поднимается testcontainers'ом (`postgres:16-alpine`), схема пересоздаётся
  фикстурой `db_init`, очистка — `clear_db` (truncate).
- schemathesis гоняет запросы в **живой uvicorn-сервер** (фикстура
  `live_server_url`) — ровно из-за привязки asyncpg к loop'у. Не заменяй на
  ASGI-транспорт.
- Миграционные тесты помечены `slow` и работают в отдельной БД `alembic_test`
  (пересоздаётся на каждый тест). pytest-alembic синхронный — потому dev-зависимость
  `psycopg[binary]`.
- Тест `test_api` — property-based: он сам находит дыры контракта (недокументированные
  статусы, отсутствие границ). Если он упал — почти всегда это реальный баг
  схемы/эндпоинта, а не теста. Чек `allow_header_conformance` отключён
  (квёрк starlette: неполный `Allow` на 405).
- Для нового эндпоинта тесты писать не обязательно — schemathesis покроет
  контракт автоматически; юнит-тесты юзкейсов приветствуются.

## Грабли (выстрадано)

1. `ENVIRONMENT` ≠ `COMMON__ENVIRONMENT` — второе.
2. Убрал границы у id/строки → лови 500 из PG (int32 overflow, NUL-байты).
3. Поменял request-схему — проверь response-схему (см. правило выше).
4. Тесты падают «different loop» → смотри пункт про loop scope.
5. Упал `test_model_definitions_match_ddl` → модель не зарегистрирована в
   `enabled_migration_models.py` или миграция расходится с моделью.
6. После изменения `pyproject.toml` — `uv lock` и проверь, что `.pre-commit-config.yaml`
   версии совпадают.
7. `chmod 777`, `curl`, компиляторы в prod-образе — не возвращать; рантайм-образ
   чистый (см. Dockerfile).

## Чего не делать

- Не коммитить `.env`, `uv.lock` наоборот — коммитить всегда.
- Не удалять CSRF-мидлварь (`csrf_middleware.py`) — оставлена осознанно.
- Не заводить «свои» форматы ошибок рядом с `BaseError`/`ErrorSchema`.
- Не поднимать БД/Redis в тестах мимо фикстур conftest.
- Не использовать `ORJSONResponse` (deprecated) и poetry-команды (проект на uv).
