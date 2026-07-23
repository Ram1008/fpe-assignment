# Makefile for AI Decision-Tree Agent Project

.PHONY: help install run build test clean backend frontend

help:
	@echo "AI Decision-Tree Agent Commands:"
	@echo "  make install   - Install backend and frontend dependencies"
	@echo "  make run       - Run backend server and frontend development server"
	@echo "  make backend   - Run FastAPI backend server (port 8000)"
	@echo "  make frontend  - Run React Vite frontend (port 3000)"
	@echo "  make test      - Run automated test suite (backend & frontend tests)"
	@echo "  make clean     - Clean temporary files and caches"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

run:
	@echo "Starting AI Decision-Tree Agent..."
	python run_dev.py

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	@echo "Running backend test suite..."
	cd backend && pytest -v
	@echo "Running frontend tests..."
	cd frontend && npm run test -- --run

clean:
	rm -rf backend/__pycache__ backend/.pytest_cache frontend/dist frontend/node_modules/.cache
