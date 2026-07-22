.PHONY: bootstrap dev down test lint format typecheck check worker

bootstrap:
	cp .env.example .env

dev:
	docker compose up --build -d

down:
	docker compose down

test:
	pytest

lint:
	ruff check .

format:
	ruff format --check .

typecheck:
	mypy apps packages tests

check: format lint typecheck test

worker:
	celery --app apps.worker.worker.celery_app:celery_app worker --loglevel=INFO
