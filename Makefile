# Makefile for Second Brain Agent
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev test test-unit test-integration test-e2e coverage lint format clean run-architect run-dev

help:
	@echo "Second Brain Agent - Development Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-e2e         Run end-to-end tests only"
	@echo "  make coverage         Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (flake8, pylint)"
	@echo "  make format           Format code (black, isort)"
	@echo "  make type-check       Run mypy type checking"
	@echo "  make quality          Run all quality checks"
	@echo ""
	@echo "Running:"
	@echo "  make run-architect    Run architect CLI"
	@echo "  make run-dev          Run dev team CLI"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and cache"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit -v -m "not slow"

test-integration:
	pytest tests/integration -v

test-e2e:
	pytest tests/e2e -v

coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Code Quality
lint:
	@echo "Running flake8..."
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	@echo "Running pylint..."
	pylint src/ --max-line-length=100 --disable=C0114,C0115,C0116

format:
	@echo "Running black..."
	black src/ tests/ --line-length=100
	@echo "Running isort..."
	isort src/ tests/ --profile=black --line-length=100

type-check:
	mypy src/ --ignore-missing-imports

quality: format lint type-check
	@echo "All quality checks passed!"

# Running applications
run-architect:
	python architect.py

run-dev:
	python dev_team.py

run-curator:
	python curator.py

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage
	@echo "Cleanup complete!"

# Development setup
setup: install-dev
	@echo "Setting up development environment..."
	mkdir -p logs output
	@echo "Development environment ready!"


# ============================================================================
# Phase 2: Enhanced CLI Commands
# ============================================================================

# Test new CLI
cli-test:
	@echo "Testing enhanced CLI..."
	sba --help
	sba version
	sba info

# Demo architect with enhanced CLI
demo-architect:
	@echo "Demo: Generating TDD from job description..."
	sba architect --job "Build a REST API for task management with user authentication" --output demo-tdd.md

# Demo dev team with enhanced CLI
demo-dev:
	@echo "Demo: Generating code from TDD..."
	sba dev-team --tdd demo-tdd.md --output ./demo-project

# Full demo workflow
demo-full: demo-architect demo-dev
	@echo "Demo complete! Check ./demo-project"

# Clean demo files
clean-demo:
	@echo "Cleaning demo files..."
	rm -f demo-tdd.md
	rm -rf demo-project

# Test Phase 2 features
test-phase2:
	@echo "Testing Phase 2 features..."
	python -c "from src.cli.main import app; print('✓ CLI module')"
	python -c "from src.utils.output_manager import OutputManager; print('✓ Output Manager')"
	python -c "from src.core.settings import settings; print('✓ Settings:', settings.default_model)"
	python -c "from src.utils.progress import ProjectProgress; print('✓ Progress Tracking')"
	@echo "All Phase 2 features loaded successfully!"

# Interactive demo with progress tracking
demo-interactive:
	@echo "Running interactive demo..."
	python -c "from src.utils.progress import example_simple_progress; example_simple_progress()"
