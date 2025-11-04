import asyncio
import os
import sys

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import config as app_config
from migrations.enabled_migration_models import BaseDBModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

config = context.config
fileConfig(config.config_file_name)

if len(config.get_section(config.config_ini_section).get('sqlalchemy.url')) == 0:
    config.set_main_option(
        'sqlalchemy.url',
        app_config.postgres.database_uri.render_as_string(hide_password=False),
    )

target_metadata = BaseDBModel.metadata
target_schemas = list(target_metadata._schemas)

version_schema = '__alembic_schema'
enabled_pg_schemas: list = [
    '__alembic_schema',
    'template_schema',
]

for schema in target_schemas:
    if schema not in enabled_pg_schemas:
        raise Exception(
            'Add new schema(s) in enable_schemas or fix schema name typo in detected table(s)',
        )


def include_object(object, name, type_, reflected, compare_to):
    """Функция-признак, показывающая, учитывается ли объект при автогенрации.

    Вызываемая функция, которой предоставляется возможность вернуть True или False
    для любого объекта, указывая, должен ли данный объект учитываться при автогенерации.
    https://alembic.sqlalchemy.org/en/latest/api/runtime.html
    #alembic.runtime.environment.EnvironmentContext.configure.params.include_object.

    Args:
        object: объект SchemaItem, такой, как объект Table, Column,
            Index UniqueConstraint или ForeignKeyConstraint
        name: имя объекта. Обычно оно доступно через object.name
        type_: строка, описывающая тип объекта; в настоящее время
            "table", "column", "index", "unique_constraint", "foreign_key_constraint"
        reflected: True, если данный объект был создан на основе отражения таблицы,
            False, если он получен из локального объекта MetaData.
        compare_to: объект, c которым сравнивается, если доступен, иначе None
    """

    # # He добавляем рефлексивные колонки
    # if type_ == "column" and not reflected:
    #     return False
    if type_ == 'table' and object.schema not in enabled_pg_schemas:
        return False

    return True


def include_name(name, type_, parent_names) -> bool:
    """Функция-признак включения имени сущности.

    Вызываемая функция, которой предоставляется возможность возвращать True или False
    для любого отраженного объекта базы данных на основе ero имени,
    включая имена схем баз данных
    https://alembic.sqlalchemy.org/en/latest/api/runtime.html
    #alembic.runtime.environment.EnvironmentContext.configure.params.include_name.

    Args:
        name: имя объекта, например, имя схемы или имя таблицы.
            Будет равно None при указании имени схемы по умолчанию
            для подключения к базе данных
        type_: строка, описывающая тип объекта; в настоящее время
            "schema", "table", "column", "index", "unique_constraint"
             или "foreign_key_constraint"
        parent_names:
            словарь имен "родительских" объектов, которые являются относительными
            по отношению к задаваемому имени. Ключи в этом словаре
            могут включать: "имя_схемы", "имя_таблицы".

    Returns:
        Boolean
    """

    if type_ == 'schema':
        # this **will* include the default schema
        return name in enabled_pg_schemas

    return True


def process_revision_directives(context, revision, directives):
    """Этот код нужен для тестирования алембик миграций.

    Вызываемая функция, которой будет передана структура, представляющая конечный
    результат операции автогенерации или простой операции "ревизии". Ей можно
    манипулировать, чтобы повлиять на то, как команда alembic revision в
    конечном итоге выводит новые скрипты ревизии.

    https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.
    environment.EnvironmentContext.configure.params.process_revision_directives

    Args:
        context: это используемый MigrationContext
            https://alembic.sqlalchemy.org/en/latest/api/runtime.html
            #alembic.runtime.migration.MigrationContext
        revision: кортеж идентификаторов ревизий, представляющих текущую
            ревизию базы данных
        directives: Параметр directives представляет собой список Python, содержащий
            одну директиву MigrationScript и представляет файл ревизии,
            который должен быть сгенерирован. Этот список, a также ero содержимое
            можно свободно изменять для создания любого набора команд.
            B разделе Настройка генерации ревизий показан пример такой настройки.
            https://alembic.sqlalchemy.org/en/latest/api/autogenerate.html
            #customizing-revision
    """

    if config.cmd_opts.autogenerate:
        script = directives[0]
        for upgrade_ops in script.upgrade_ops_list:
            if upgrade_ops.is_empty():
                directives[:] = []


def run_migrations_offline() -> None:
    """Запуск миграции в оффлайн режиме."""

    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        echo=True,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={'paramstyle': 'named'},
        template_args={'enabled_pg_schemas': enabled_pg_schemas},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Запуск миграции в онлайн режиме."""

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        version_table_schema=version_schema,
        include_name=include_name,
        process_revision_directives=process_revision_directives,
        template_args={'enabled_pg_schemas': enabled_pg_schemas},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = async_engine_from_config(
        configuration=config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Создаем схему версии
        await connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS {version_schema}'))
        await connection.commit()
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
