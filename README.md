# Template service v2

----------------------

> В этой секции стоит дать общее описание проекта (что за проект, основное назначение,
> тезисно функционал и др.)

Сервис используется как шаблонный для создания других сервисов.

## Основной функционал:

> В этом блоке описываем все, что делает сервис:
> Например:
> - Отправка уведомлений на почту
> - Отправка пушей

## Алгоритм работы:

> В этой секции описываем основную логику работы приложения.
> ### Например:
> Сервис используется как шаблонный сервис.
> В нем реализованы основные методологии, используемые в остальных сервисах.
> - базовый круд
> - пример контроллеров
> - пример тестов (интеграционных и юнитов)
> - и тд. что необходимо знать разработчику, впервые сталкивающимся с текущим проектом

# 1. Установка

## При **первом** запуске необходимо:

Настроить переменные окружения:

#### Создать файл `.env` в корне проекта, пример можно посмотреть [тут](./env.example):

### Описание возможных ENV параметров

> Тут указываем все настройки, которые приложение использует для работы.

| Name                                   | Description                                                                                                                            | Default value                                                                            |
|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `COMMON__ENVIRONMENT`                  | Наименование текущего окружения                                                                                                        | `None`                                                                                   |
| `COMMON__LOG_LEVEL`                    | Уровень логирования ([возможные варианты](./app/api/utils/enums/log_level_enum.py))                                                    | `INFO`                                                                                   |
| `COMMON__HUMAN_READABLE_LOGS`          | Вкл./выкл. человекочитаемых логов. Если выключен, то логи складываются в словарь, с которым было бы удобно работать например в Grafana | `False`                                                                                  |
| `COMMON__DISABLED_LOG_ENDPOINT`        | Выключение логирования определенных ендпоинтов.                                                                                        | `["/health", /liveness", "/metrics", "/openapi.json", "/docs"]`                          |
| `COMMON__LOGGER_BODY_CONTENT_MAX_SIZE` | Ограничение длины строки лога, после которой лог будет обрезаться                                                                      | `2500`                                                                                   |
| `COMMON__BACKEND_CORS_ORIGINS`         | Настройки CORS                                                                                                                         | `[]`                                                                                     |
| `COMMON__PROMETHEUS_ENABLED`           | Вкл./выкл. сбора статистики для Prometheus                                                                                             | `True`                                                                                   |
| `COMMON__STRUCT_LOG`                   | Вкл./выкл. кастомного логгера                                                                                                          | `True`                                                                                   |
| `POSTGRES__USER`                       | Пользователь PG                                                                                                                        | `postgres`                                                                               |
| `POSTGRES__PASSWORD`                   | Пароль PG                                                                                                                              | `example`                                                                                |
| `POSTGRES__HOST`                       | PG хост                                                                                                                                | `localhost` (если запускаешь через docker compose, попробуй указать имя контейнера с pg) |
| `POSTGRES__PORT`                       | PG порт                                                                                                                                | `5432`                                                                                   |
| `POSTGRES__DB`                         | Имя БД PG                                                                                                                              | `template_schema`                                                                        |
| `SWAGGER__DOC_LOGIN`                   | Логин Swagger                                                                                                                          | `admin`                                                                                  |
| `SWAGGER_DOC_PASSWORD`                 | Пароль Swagger                                                                                                                         | `admin`                                                                                  |

# 2. Запуск проекта:

## 2.1. С помощью докера

> Создаем docker-compose.yml и описываем в нем профили запуска. Пример лежит в проекте

Запуск возможен в 3x вариациях:

- `docker compose up --profile app up` - запуск только текущего сервиса;
- `docker compose --profile db up` - запуск pg + redis
- `docker compose --profile dev up` - запуск сервиса + postgresql + redis +
  выполнятся миграции;

> Dockerfile собирается в несколько стадий (multi-stage): `development-image` (dev-
> зависимости и hot-reload), `alembic-image` (накат миграций), `test-image` (pytest
> + coverage) и `production-image` (лёгкий образ без компиляторов и dev-зависимостей).
> Стадия указывается через `--target <stage>` в docker build / docker-compose.

> флаг `-d` запустит контейнер в фоновом режиме
> флаг `--build` перебилдит текущий проект

## 2.2. Запуск без докера
- Устанавливаем зависимости `uv sync`;
- Ставим `pre-commit install` для линта кода;
- Устанавливаем переменные окружения
- Запускаем pg `docker compose --profile db up -d --build`;
- Запускам миграции `make migrate_with_data`;
- Запускаем приложение `make run`;

# 3. Использование

## 3.1 Запуск тестов

> Здесь можно указывать все, что связано с тестами. Допустим указать параметры для
> пропуска "долгих" тестов, какие тесты отключены и почему и тд

Все тесты (в т.ч. "долгие" тесты миграций с testcontainers):

```bash
make test_slow
```

Пропуск "долгих" тестов (маркер `slow`):

```bash
make test
```

## 3.2 Линтеры

> Блок с линтерами. Идейно пока хватает pre-commit, но мало ли что.

Запуск линтеров по всему проекту:

```bash
make lint
```

## 3.3 Миграции

> Блок с алембиком (если он нужен). Все команды доступны через Makefile
> (`make migrations_init`, `make makemigrations MSG=...`, `make migrate`,
> `make migrate_with_data`, `make downgrade`).

- `uv run alembic revision --autogenerate -m "message"` - генерация новой миграции
- `uv run alembic upgrade head` - накат миграций
- `uv run alembic -x data=true upgrade head` - накат миграций вместе с данными. Выполняется
  функция data_upgrades() в файле миграции
- `uv run alembic upgrade head --sql > migration.sql` - генерация SQL файла с миграциями.
- `uv run alembic downgrade -1` - откат миграции на 1 версию назад

# 4. Дополнительная информация

> В этом блоке указываем дополнительную информацию, которую сложно структурировать по
> существующим блокам

> В ключевых местах проекта оставлены теги *FIXME* и *TODO*.

## 4.1 Для работы с новым проектом необходимо:

### 1. "Чистка" текущего проекта:

- Удалить все миграции из папки `migrations/versions`;
- Удалить все модели из папки `app/api/v1/models`;
- Удалить все контроллеры из папки `app/api/v1/controllers`;
- Удалить лишние импорты и роуты из `app/api/v1/__init__.py`;
- Удалить файлы `role_schema.py` и `user_schema.py` из папки `app/api/v1/schemas`;
- Удалить файлы `role_crud.py` и `user_crud.py` из папки `app/api/v1/crud`;
- Удалить все тесты в папке `tests/api/v1`

### 2. Настройка проекта:

#### 2.0 Redis и Kafka (FastStream)

Оба компонента опциональны и по умолчанию Kafka выключена (`KAFKA__ENABLED=false`).
Везде, где их можно выкинуть, оставлены теги `FIXME` с точной инструкцией:

- **Redis**: секция `RedisSettings` в `app/config.py`, провайдеры
  `redis_pool_scope` / `redis_scope` в `app/api/di`, сервис `redis` в
  `docker-compose.yml`, зависимость `redis` в `pyproject.toml`.
- **Kafka**: секция `KafkaSettings` в `app/config.py`, провайдер `kafka_broker_scope`
  в `app/api/di/application.py`, блок в `_warmup_dependencies` (`app/main.py`),
  папка `app/api/v1/faststream_consumers`, зависимости `faststream` /
  `dishka-faststream` в `pyproject.toml`.

Консюмеры описываются в `app/api/v1/faststream_consumers` (см. пример в
  `example_callback.py`) и подключаются в `faststream_consumers/router.py`.

#### 2.1 Настройка миграций и моделей:

Если планируется использовать Alembic и SQLAlchemy:

- в файле `migrations/env.py` прописываем `schema = "Используемая схема"`
- описать модели и импортировать их в файл `migrations/enabled_migration_models.py` для
  включения этих моделей в миграции

Если алембик и SQLAlchemy использовать не планируется:

- Удаляем зависимости `uv remove alembic sqlalchemy asyncpg greenlet`
- Удаляем файл `alembic.ini`
- Удаляем папку `migrations`
- Удаляем папку `app/api/v1/crud` и `app/api/v1/models`
- Удаляем `pg_engine_scope` из `app/api/di/application.py` и `pg_session_scope` из
  `app/api/di/request.py`
- Удаляем из `tests/conftest.py` все фикстуры, использующие БД

### 2.2 Настройка переменных окружения

Все настройки проекта находятся в файле `app/config.py`. Конфигурация автоматически
собирает переменные из окружения. Для валидации конфига
используется `pydantic.BaseSettings` https://docs.pydantic.dev/usage/settings/

### 3. Тестирование проекта

По умолчанию подключено:

- Тесты миграций (файл `tests/api/utils/test_migrations.py`).
  test_up_down_consistency() является довольно медленным тестом при большом количестве
  миграций (маркирован `slow`);
- Тестовый клиент fastapi;
- Тест хелсчека
- Все тесты по умолчанию интеграционные, т.е. используется тестовая БД
  (поднимается через testcontainers — нужен запущенный Docker).

## 4.2 Важные дополнения

### BaseDBModel

Все модели стоит наследовать от `app/api/utils/sqlalchemy/base_db_model.py:BaseDBModel`, т.к.
базовый класс легче расширять

### BaseENUM

Все ENUM стоит так же наследовать от `app/api/utils/enums/base_enum.py:BaseENUM`.

### BaseSchema

Все схемы Pydantic так же стоит наследовать
от `app/api/v1/schemas/base_schema.py:BaseSchema`. В ней по умолчанию прописаны
корректная работа с datetime, указан декодер по умолчанию

### Controller + Usecase + FromDishka as Depends

- В контроллере всегда должен быть только юзкейс
- Юзкейс можно вызвать только FromDishka сразу со всеми его зависимостями, т.е. Если в
  юзкейсе будет использована сессия пг или использован какой нибудь клиент например в
  гпт, то эти элементы должны быть определены в провайдере Dishka и инициализированы
  вместе с юзкейсом.
- Отсюда все классы кроме CRUD (тут как кому удобно) и различных DTO так или иначе
  должны быть "зарегистрированы" в провайдерах.

### Работа c Makefile

`Makefile` это удобный способ назначать короткие
для запоминания имена для "длинных" команд.

Допустим у Вас есть команда `alembic upgrade head`,
которая применяет миграцию.

Вы можете назначить ей удобное короткое,
для запоминания имя в файле `Makefile`:

``` sh
migrate:
	alembic upgrade head
```

Теперь Вам достаточно ввести в консоли:

``` sh
make migrate
```

Искомая команда будет выполнена.
