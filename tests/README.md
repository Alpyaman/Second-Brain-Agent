# Tests

This directory contains all tests for Second Brain Agent.

## Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests (fast, isolated)
│   ├── test_validators.py
│   ├── test_exceptions.py
│   └── test_utils.py
├── integration/         # Integration tests (multiple components)
│   ├── test_architect_workflow.py
│   └── test_dev_team_workflow.py
└── e2e/                 # End-to-end tests (full pipeline)
    └── test_full_pipeline.py
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test types
```bash
# Unit tests only (fast)
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# End-to-end tests only (slow)
pytest tests/e2e -v
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html
```

### Run specific test file
```bash
pytest tests/unit/test_validators.py -v
```

### Run specific test
```bash
pytest tests/unit/test_validators.py::TestJobDescriptionValidation::test_valid_job_description -v
```

## Writing Tests

### Unit Tests
- Test individual functions/methods in isolation
- Use mocks for external dependencies
- Should be fast (<0.1s per test)

### Integration Tests
- Test multiple components working together
- May use real databases/services in test mode
- Can be slower (0.1s - 2s per test)

### E2E Tests
- Test complete workflows from start to finish
- Use real or near-real environments
- Can be slow (2s+ per test)

## Coverage Goals

- Unit tests: 80%+ coverage
- Integration tests: 60%+ coverage
- Critical paths: 90%+ coverage
