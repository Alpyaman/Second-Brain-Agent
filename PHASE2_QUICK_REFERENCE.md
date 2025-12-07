# Phase 2 Quick Reference

## 🚀 Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install package in development mode
pip install -e .

# 3. Verify installation
python scripts/verify_phase2.py
```

## 📋 CLI Commands

### Architect (Generate TDD)

```bash
# Basic usage
sba architect --job "Build a REST API"

# From file
sba architect --job-file job.txt --output design.md

# Interactive mode
sba architect --job-file job.txt --interactive

# Specify model
sba architect --job "..." --model gemini-pro

# Skip validation (faster)
sba architect --job "..." --no-validate
```

### Dev Team (Generate Code)

```bash
# Basic usage
sba dev-team --tdd design.md --output ./my-project

# Specify frameworks
sba dev-team --tdd design.md --framework django --frontend nextjs

# Run specific phase
sba dev-team --tdd design.md --phase 1

# Without Docker
sba dev-team --tdd design.md --no-docker

# Skip validation
sba dev-team --tdd design.md --no-validate
```

### Info Commands

```bash
# Show version
sba version

# Show system info
sba info

# Get help
sba --help
sba architect --help
sba dev-team --help
```

## 🔧 Configuration (.env)

```env
# API Keys
GOOGLE_API_KEY=your_google_api_key

# Model Settings
DEFAULT_MODEL=gemini-pro
MAX_TOKENS=4096
TEMPERATURE=0.7

# Frameworks
BACKEND_FRAMEWORK=fastapi
FRONTEND_FRAMEWORK=react

# Paths
OUTPUT_DIR=./output

# Features
INCLUDE_DOCKER=true
INCLUDE_TESTS=true
ENABLE_CACHING=true
LOG_LEVEL=INFO
```

## 🛠️ Makefile Commands

```bash
# Test Phase 2 features
make test-phase2

# Test CLI
make cli-test

# Demo architect
make demo-architect

# Demo dev team
make demo-dev

# Full demo workflow
make demo-full

# Clean demo files
make clean-demo

# Interactive demo
make demo-interactive
```

## 💻 Python API

### Output Manager

```python
from src.utils.output_manager import OutputManager

manager = OutputManager(base_dir="./output")
project_dir = manager.create_project_dir("my-app")
files = manager.save_structured_output(project_dir, state)
```

### Settings

```python
from src.core.settings import settings

# Access settings
print(settings.default_model)
print(settings.max_tokens)

# Check API keys
if settings.has_api_key('google'):
    print("Ready!")

# Get model config
config = settings.get_model_config()
```

### Progress Tracking

```python
from src.utils.progress import ProjectProgress

progress = ProjectProgress("Generating Code")
stages = ["Parse", "Backend", "Frontend"]

with progress.track_generation(stages) as update:
    for stage in stages:
        update(stage)
        # do work...
```

## 📁 Generated Project Structure

```
output/my-app_20241207_143022/
├── backend/
│   ├── src/main.py
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/App.tsx
│   ├── package.json
│   └── Dockerfile
├── docs/
│   ├── DESIGN.md
│   ├── ARCHITECTURE.md
│   └── API.md
├── docker-compose.yml
├── README.md
├── .gitignore
└── .sba_metadata.json
```

## 🔍 Troubleshooting

### Command not found

```bash
# Reinstall package
pip install -e .
```

### Import errors

```bash
# Update dependencies
pip install -r requirements.txt --upgrade
```

### Settings not loading

```bash
# Check .env exists
ls -la .env

# Test settings
python -c "from src.core.settings import settings; print(settings.default_model)"
```

## 📚 Documentation

- **Phase 2 Summary:** `docs/PHASE2_SUMMARY.md`
- **Examples:** `docs/PHASE2_EXAMPLES.md`
- **User Guide:** `docs/USER_GUIDE.md`

## ✅ Verification

```bash
# Run verification script
python scripts/verify_phase2.py

# Expected output:
# ✅ All checks passed! Phase 2 is ready to use.
```

## 🎯 Quick Workflow

```bash
# 1. Generate TDD
sba architect --job-file job.txt --output design.md

# 2. Generate code
sba dev-team --tdd design.md --output ./my-project

# 3. Run the project
cd my-project
docker-compose up

# 4. Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 🆚 Old vs New Commands

| Old | New | Status |
|-----|-----|--------|
| `python architect.py ...` | `sba architect ...` | Both work |
| `python dev_team.py ...` | `sba dev-team ...` | Both work |
| Manual output management | Auto-generated structure | New feature |
| No progress indicators | Rich progress bars | New feature |
| Hardcoded settings | .env configuration | New feature |

## 🎨 Features Overview

| Feature | Description | Location |
|---------|-------------|----------|
| Enhanced CLI | Modern terminal UI | `src/cli/main.py` |
| Output Manager | Auto project structure | `src/utils/output_manager.py` |
| Settings | Type-safe config | `src/core/settings.py` |
| Progress | Visual feedback | `src/utils/progress.py` |

## 📞 Support

- Check documentation: `docs/`
- Run verification: `python scripts/verify_phase2.py`
- Review examples: `docs/PHASE2_EXAMPLES.md`
- Check logs: `logs/`
