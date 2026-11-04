PORT:=8000

deps-up:
	docker compose --profile db up -d postgresql redis

run:
	uv run uvicorn app.main:app --host 127.0.0.1 --port "$(PORT)"

migrations_init:
	uv run alembic revision --autogenerate -m "init"

makemigrations:
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate:
	uv run alembic upgrade head

migrate_with_data:
	uv run alembic -x data=true upgrade head

downgrade:
	uv run alembic downgrade -1

test_slow:
	uv run pytest --maxfail=1 --cov=app -vv --cov-config .coveragerc -m slow

test:
	uv run pytest --maxfail=1 --cov=app -vv --cov-config .coveragerc -m "not slow"

lint:
	uv run pre-commit run --all-files
