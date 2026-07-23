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

eval-golden:
	python -c "from packages.application.eval_cli import validate; validate()"

eval-smoke:
	python -m packages.application.eval_cli

eval-regression: eval-smoke

.PHONY: web-install web-dev web-lint web-typecheck web-test web-build web-e2e-mock
web-install:
	npm --prefix apps/web ci
web-dev:
	npm --prefix apps/web run dev
web-lint:
	npm --prefix apps/web run lint
web-typecheck:
	npm --prefix apps/web run typecheck
web-test:
	npm --prefix apps/web run test
web-build:
	npm --prefix apps/web run build
web-e2e-mock:
	npm --prefix apps/web run e2e:mock
