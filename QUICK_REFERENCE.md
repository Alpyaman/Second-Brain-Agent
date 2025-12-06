# Quick Reference Guide

## 🚀 Quick Commands

### Installation
```bash
# Install production dependencies
make install

# Install development dependencies
make install-dev

# Or use the setup script
bash scripts/setup_dev.sh        # Linux/Mac
scripts\setup_dev.bat            # Windows
```

### Testing
```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make coverage          # Run with coverage report
```

### Code Quality
```bash
make format            # Format code (black + isort)
make lint              # Run linters (flake8 + pylint)
make type-check        # Run mypy type checking
make quality           # Run all quality checks
```

### Running the Application
```bash
make run-architect     # Run architect CLI
make run-dev          # Run dev team CLI
make run-curator      # Run curator CLI

# Or directly
python architect.py
python dev_team.py
```

### Cleanup
```bash
make clean            # Remove build artifacts and cache
```

---

## 📦 New Modules Usage

### Using Validators
```python
from src.utils.validators import (
    validate_job_description,
    validate_tdd_file,
    validate_output_directory
)

# Validate job description
is_valid, error = validate_job_description(job_text)
if not is_valid:
    print(f"Validation failed: {error}")

# Validate TDD file
is_valid, error = validate_tdd_file(Path("design.md"))
```

### Using Custom Exceptions
```python
from src.utils.exceptions import (
    ValidationError,
    LLMError,
    OutputGenerationError
)

# Raise validation error
if not is_valid:
    raise ValidationError("Invalid job description", details={"length": len(text)})

# Catch specific errors
try:
    result = call_llm_api()
except LLMError as e:
    logger.error(f"LLM error: {e}")
```

### Using Logger
```python
from src.utils.logger import setup_project_logger

# Set up logger for your component
logger = setup_project_logger("my_component")

logger.info("Processing started")
logger.warning("API key not found")
logger.error("Failed to generate code", exc_info=True)
```

### Using Constants
```python
from src.constants import (
    AgentType,
    LLMProvider,
    ModelName,
    ProjectType,
    Framework,
    Database,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE
)

# Use enums
agent_type = AgentType.ARCHITECT
model = ModelName.GEMINI_PRO
framework = Framework.FASTAPI
```

---

## 🧪 Writing Tests

### Unit Test Example
```python
# tests/unit/test_my_module.py
import pytest
from src.my_module import my_function

def test_my_function():
    """Test my_function with valid input."""
    result = my_function("input")
    assert result == "expected"

def test_my_function_invalid():
    """Test my_function with invalid input."""
    with pytest.raises(ValueError):
        my_function(None)
```

### Using Fixtures
```python
def test_with_fixtures(sample_job_description, temp_dir):
    """Test using shared fixtures."""
    output_file = temp_dir / "output.txt"
    process_job(sample_job_description, output_file)
    assert output_file.exists()
```

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```bash
# API Keys
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Model Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=codellama
DEFAULT_MODEL=gemini-pro

# Paths
OUTPUT_DIR=./output
CHROMA_DB_DIR=./src/data/chroma_db
```

---

## 📝 Commit Message Format

```
<type>: <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

Examples:
```
feat: add validation for TDD files
fix: handle missing API keys gracefully
docs: update contributing guide
test: add unit tests for validators
```

---

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
from src.utils.logger import setup_project_logger

logger = setup_project_logger("my_component", level=logging.DEBUG)
```

### Run Tests with Verbose Output
```bash
pytest tests/ -v -s
```

### Run Specific Test
```bash
pytest tests/unit/test_validators.py::TestJobDescriptionValidation::test_valid_job_description -v
```

---

## 📊 Project Metrics

### View Test Coverage
```bash
make coverage
# Open htmlcov/index.html in browser
```

### Check Code Quality
```bash
make lint
```

### View Logs
```bash
cat logs/architect_20241206.log
cat logs/dev_team_20241206.log
```

---

## 🆘 Common Issues

### Issue: Import errors
**Solution**: Make sure you're in the virtual environment
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### Issue: Tests failing
**Solution**: Install dev dependencies
```bash
make install-dev
```

### Issue: Pre-commit hooks failing
**Solution**: Format code before committing
```bash
make format
```

### Issue: Module not found
**Solution**: Install in editable mode
```bash
pip install -e .
```

---

## 📚 Additional Resources

- **Full Documentation**: See `docs/` directory
- **Contributing**: See `CONTRIBUTING.md`
- **Project Structure**: See `PROJECT_STRUCTURE.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`

---

**Last Updated**: December 2024
**Version**: 0.1.0
