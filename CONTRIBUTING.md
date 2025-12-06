# Contributing to Second Brain Agent

Thank you for your interest in contributing to Second Brain Agent! This guide will help you get started.

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/yourusername/Second-Brain-Agent.git
cd Second-Brain-Agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install development dependencies
make install-dev

# Or manually
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### 4. Set Up Environment Variables

Create a `.env` file:

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Code Quality Standards

### Code Formatting

We use **Black** for code formatting and **isort** for import sorting:

```bash
# Format all code
make format

# Or manually
black src/ tests/ --line-length=100
isort src/ tests/ --profile=black
```

### Linting

We use **flake8** and **pylint**:

```bash
# Run all linters
make lint
```

### Type Checking

We use **mypy** for static type checking:

```bash
make type-check
```

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit:

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run with coverage
make coverage
```

### Writing Tests

#### Unit Tests (`tests/unit/`)

Test individual functions in isolation:

```python
def test_validate_job_description():
    """Test job description validation."""
    is_valid, error = validate_job_description("Build a REST API...")
    assert is_valid is True
```

#### Integration Tests (`tests/integration/`)

Test multiple components together:

```python
def test_architect_to_dev_workflow(sample_job_description):
    """Test complete workflow from job description to code."""
    design = run_architect(sample_job_description)
    code = run_dev_team(design)
    assert code is not None
```

### Test Coverage

- Aim for 80%+ coverage on new code
- All bug fixes must include tests
- Critical paths require 90%+ coverage

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test additions/improvements

### 2. Make Your Changes

- Follow existing code style
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

### 3. Run Quality Checks

```bash
# Run all quality checks
make quality

# Or run individually
make format
make lint
make type-check
make test
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new validation for job descriptions"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `style:` - Formatting changes
- `chore:` - Maintenance tasks

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Project Structure

```
Second-Brain-Agent/
├── src/
│   ├── agents/          # Agent implementations
│   ├── core/            # Core functionality
│   ├── tools/           # Tools and utilities
│   ├── ingestion/       # Code ingestion
│   ├── utils/           # Helper functions
│   └── constants/       # Constants and enums
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── output/              # Generated projects
```

## Coding Guidelines

### Python Style

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Keep functions small and focused
- Use meaningful variable names

### Example Function

```python
def validate_job_description(text: str, min_length: int = 50) -> Tuple[bool, str]:
    """
    Validate job description input.

    Args:
        text: The job description text to validate
        min_length: Minimum required length in characters

    Returns:
        Tuple of (is_valid, error_message)

    Raises:
        ValidationError: If validation fails critically

    Example:
        >>> is_valid, error = validate_job_description("Build a REST API...")
        >>> print(is_valid)
        True
    """
    # Implementation
    pass
```

### Error Handling

- Use custom exceptions from `src.utils.exceptions`
- Provide clear error messages
- Log errors appropriately
- Never swallow exceptions silently

### Logging

```python
from src.utils.logger import setup_project_logger

logger = setup_project_logger("my_module")
logger.info("Processing started")
logger.error("Error occurred", exc_info=True)
```

## Documentation

### Code Documentation

- All public functions need docstrings
- Use Google-style docstrings
- Include examples where helpful
- Document parameters and return values

### User Documentation

- Update README.md for user-facing changes
- Add usage examples
- Keep documentation in sync with code

## Getting Help

- **Issues**: Search existing issues or create a new one
- **Discussions**: Ask questions in GitHub Discussions
- **Discord**: Join our community Discord (coming soon)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
