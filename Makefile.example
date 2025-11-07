PORT:=8000

run:
	uvicorn app.main:app --host 127.0.0.1 --port "$(PORT)"

migrations_init:
	alembic revision --autogenerate -m "init"

makemigrations:
	alembic revision --autogenerate -m "$(MSG)"

migrate:
	alembic upgrade head

migrate_with_data:
	alembic -x data=true upgrade head

downgrade:
	alembic downgrade -1

test_long:
	pytest --maxfail=1 --cov=app -vv --cov-config .coveragerc

test:
	pytest --maxfail=1 --cov=app -vv --cov-config .coveragerc -m "not long"

lint:
	pre-commit run --all-files
