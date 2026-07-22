.PHONY: dev test lint typecheck check

dev:
	docker compose -f ../docker-compose.yml up -d

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy apps packages

check: lint typecheck test
