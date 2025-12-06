#!/bin/bash
# Quick setup script for Second Brain Agent development environment

echo "=================================="
echo "Second Brain Agent - Dev Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

# Install production dependencies
echo "Installing production dependencies..."
pip install -r requirements.txt
echo "✓ Production dependencies installed"
echo ""

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt
echo "✓ Development dependencies installed"
echo ""

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install
echo "✓ Pre-commit hooks installed"
echo ""

# Create necessary directories
echo "Creating project directories..."
mkdir -p logs output
echo "✓ Directories created"
echo ""

echo "=================================="
echo "Setup Complete! ✅"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Activate venv: source venv/bin/activate"
echo "2. Copy .env.example to .env and add your API keys"
echo "3. Run tests: make test"
echo "4. Start coding!"
echo ""
echo "Available commands:"
echo "  make help          Show all available commands"
echo "  make test          Run tests"
echo "  make format        Format code"
echo "  make lint          Run linters"
echo ""
