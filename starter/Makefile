.PHONY: dev test lint typecheck

dev:
	docker compose -f docker-compose.dev.yml up -d

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy apps packages
