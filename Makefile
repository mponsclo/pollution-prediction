.PHONY: help install dbt-build train predict serve dashboard frontend sync-outputs mlflow-ui log-experiments \
       docker-build docker-run docker-compose-up docker-compose-down test lint format clean

PYTHON ?= python
PIP ?= pip

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Setup ---

install: ## Install all dependencies
	$(PIP) install -r requirements.txt

dbt-build: ## Run DBT pipeline (seed + build + test)
	cd dbt_pollution && dbt build

# --- ML ---

train: ## Train all models with MLflow tracking
	$(PYTHON) scripts/train_with_mlflow.py --task forecast --all
	$(PYTHON) scripts/train_with_mlflow.py --task anomaly --all

predict: ## Export trained models for API serving
	$(PYTHON) scripts/export_models.py

log-experiments: ## Log historical experiments to MLflow
	$(PYTHON) scripts/log_experiments.py

# --- Serving ---

serve: ## Start FastAPI prediction server (port 8080)
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

dashboard: ## Start Streamlit dashboard (port 8501)
	streamlit run streamlit_air_quality_dashboard.py

frontend: ## Start Next.js dashboard (port 3000, reads outputs/ locally)
	cd frontend && PREDICTIONS_LOCAL_DIR=../outputs GCP_PROJECT_ID=mpc-pollution-331382 npm run dev

sync-outputs: ## Upload prediction CSVs to the artifacts bucket
	$(PYTHON) scripts/sync_outputs_to_gcs.py

mlflow-ui: ## Start MLflow UI (port 5000)
	mlflow ui --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///mlflow.db

# --- Docker ---

docker-build: ## Build Docker image
	docker build -t bigquery-air-quality-forecasting .

docker-run: ## Run API container
	docker run -p 8080:8080 bigquery-air-quality-forecasting

docker-compose-up: ## Start all services (API + MLflow + Dashboard)
	docker compose up -d

docker-compose-down: ## Stop all services
	docker compose down

# --- Quality ---

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

lint: ## Run ruff check + format check
	ruff check .
	ruff format --check .

format: ## Auto-fix lint issues and format code
	ruff check --fix .
	ruff format .

clean: ## Remove caches and temp files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/
