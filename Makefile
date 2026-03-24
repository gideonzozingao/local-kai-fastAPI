.PHONY: help run dev docker-up docker-down migrate test lint format seed

help:
	@echo "Food Ordering API - Available Commands"
	@echo "======================================"
	@echo "  make run          Start the API server (production mode)"
	@echo "  make dev          Start with hot-reload (development)"
	@echo "  make docker-up    Start full stack with Docker Compose"
	@echo "  make docker-down  Stop all Docker containers"
	@echo "  make migrate      Run database migrations"
	@echo "  make makemig      Create a new migration"
	@echo "  make test         Run the test suite"
	@echo "  make lint         Lint with flake8"
	@echo "  make format       Format with black + isort"
	@echo "  make celery       Start Celery worker"
	@echo "  make flower       Start Flower monitoring UI"
	@echo "  make seed         Seed the database with sample data"

run:
	uvicorn app.main:app --host 0.0.0.0 --port 3432

dev:
	uvicorn app.main:app --host localhost --port 3432 --reload

docker-up:
	docker compose up -d --build
	@echo "API running at http://localhost:8000"
	@echo "Docs at http://localhost:8000/docs"
	@echo "Flower at http://localhost:5555"

docker-down:
	docker compose down

migrate:
	alembic upgrade head

makemig:
	alembic revision --autogenerate -m "$(msg)"

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=app --cov-report=html
	@echo "Coverage report at htmlcov/index.html"

lint:
	flake8 app/ tests/ --max-line-length=120 --ignore=E501,W503

format:
	black app/ tests/ --line-length=120
	isort app/ tests/

celery:
	celery -A app.workers.celery_app worker --loglevel=info

flower:
	celery -A app.workers.celery_app flower --port=5555

seed:
	python scripts/seed.py
