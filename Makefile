.PHONY: help build up down restart logs clean test

help:
	@echo "MLOps Docflow - Makefile commands:"
	@echo ""
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - Show logs from all services"
	@echo "  make logs-api    - Show logs from inference API"
	@echo "  make logs-airflow - Show logs from Airflow"
	@echo "  make clean       - Remove all containers, volumes, and images"
	@echo "  make test        - Run tests (if available)"
	@echo "  make shell-api   - Open shell in inference API container"
	@echo "  make db-init     - Initialize database"
	@echo ""

build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo ""
	@echo "Services started! Access points:"
	@echo "  API:        http://localhost:8000/docs"
	@echo "  Airflow:    http://localhost:8080 (admin/admin)"
	@echo "  MLflow:     http://localhost:5000"
	@echo "  MinIO:      http://localhost:9001 (minioadmin/minioadmin123)"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3000 (admin/admin)"

down:
	@echo "Stopping services..."
	docker-compose down

restart: down up

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f inference-api

logs-airflow:
	docker-compose logs -f airflow-scheduler airflow-webserver

logs-mlflow:
	docker-compose logs -f mlflow

clean:
	@echo "Removing all containers, volumes, and images..."
	docker-compose down -v --rmi all
	@echo "Cleaning local data..."
	rm -rf data/raw/* data/processed/* data/models/*
	rm -rf logs/*.log

test:
	@echo "Running tests..."
	pytest tests/ -v

shell-api:
	docker-compose exec inference-api /bin/bash

shell-airflow:
	docker-compose exec airflow-webserver /bin/bash

db-init:
	@echo "Initializing database..."
	docker-compose exec postgres psql -U mlops -d mlops_docflow -f /docker-entrypoint-initdb.d/init-db.sql

ps:
	docker-compose ps

stats:
	docker stats

install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	pip install pytest black flake8 mypy

format:
	@echo "Formatting code..."
	black services/

lint:
	@echo "Linting code..."
	flake8 services/

