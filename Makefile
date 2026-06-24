.PHONY: install install-dev lint format typecheck test test-cov clean docker-up docker-down migrate

install:
	poetry install --only main

install-dev:
	poetry install
	poetry run pre-commit install

lint:
	poetry run ruff check src/ tests/

format:
	poetry run ruff format src/ tests/
	poetry run ruff check --fix src/ tests/

typecheck:
	poetry run mypy src/

test:
	poetry run pytest tests/unit/

test-cov:
	poetry run pytest tests/ --cov=src/data_catalog --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

test-integration:
	poetry run pytest tests/integration/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

docker-logs:
	docker compose -f docker/docker-compose.yml logs -f api

migrate:
	poetry run alembic upgrade head

migrate-create:
	poetry run alembic revision --autogenerate -m "$(name)"

run-api:
	poetry run uvicorn data_catalog.api.main:app --reload --host 0.0.0.0 --port 8000
