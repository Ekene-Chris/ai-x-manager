.PHONY: help build run stop logs clean test format install dev

help:
	@echo "AI X Account Manager - Available Commands:"
	@echo ""
	@echo "  make install      - Install dependencies locally"
	@echo "  make dev          - Run development server locally"
	@echo "  make test         - Run tests"
	@echo "  make format       - Format code with black"
	@echo ""
	@echo "  make build        - Build Docker image"
	@echo "  make run          - Run application in Docker"
	@echo "  make stop         - Stop Docker containers"
	@echo "  make logs         - View Docker logs"
	@echo "  make clean        - Clean up Docker resources"
	@echo ""
	@echo "  make up           - Start with docker-compose"
	@echo "  make down         - Stop docker-compose"
	@echo "  make restart      - Restart docker-compose"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

format:
	black app/

build:
	docker build -t ai-x-manager:latest .

run:
	docker run -d \
		--name ai-x-manager \
		-p 8000:8000 \
		--env-file .env \
		ai-x-manager:latest

stop:
	docker stop ai-x-manager || true
	docker rm ai-x-manager || true

logs:
	docker logs -f ai-x-manager

clean: stop
	docker rmi ai-x-manager:latest || true

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

ps:
	docker-compose ps
