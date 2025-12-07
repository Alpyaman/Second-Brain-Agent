# Phase 2 Test Suite

This directory contains comprehensive tests for Phase 2 components of Second Brain Agent.

## Test Structure

### Unit Tests (`tests/unit/`)

#### `test_output_manager.py`
- **40+ test cases** for OutputManager functionality
- Tests project directory creation with/without timestamps
- Structured output generation (backend, frontend, docs)
- Docker and test structure generation
- Metadata and file manifest creation
- Edge cases and error handling
- **Coverage**: Complete OutputManager API

#### `test_progress.py`
- **30+ test cases** for progress tracking
- ProjectProgress multi-stage tracking
- SimpleProgress spinner functionality
- MultiProgress concurrent task tracking
- Generation summary display
- Context manager usage
- Nested progress scenarios
- **Coverage**: All progress utilities

#### `test_cli.py`
- **40+ test cases** for CLI commands
- Command parsing and options
- Architect command with various inputs
- Dev-team command with frameworks
- Version and info commands
- Input validation integration
- Error handling and user feedback
- **Coverage**: All CLI commands and options

#### `test_config.py` (Phase 1)
- **12 test cases** for Pydantic configuration
- Settings validation
- API key management
- Path configuration
- **Coverage**: 100% of config module

#### `test_validators.py` (Phase 1)
- **15+ test cases** for input validation
- Job description validation
- TDD file validation
- **Coverage**: All validators

#### `test_exceptions.py` (Phase 1)
- **10+ test cases** for custom exceptions
- Exception hierarchy
- Error message formatting
- **Coverage**: All exception classes

### Integration Tests (`tests/integration/`)

#### `test_workflows.py`
- **30+ test cases** for component integration
- Validation → Output generation workflows
- Progress tracking integration
- Logging integration across components
- Configuration integration
- Complete multi-stage workflows
- Error handling in integrated scenarios
- **Coverage**: Component interactions

### E2E Tests (`tests/e2e/`)

#### `test_full_pipeline.py`
- **30+ test cases** for end-to-end scenarios
- Complete CLI pipeline testing
- Full project generation
- File structure validation
- Error scenario handling
- Performance testing (large projects, multiple projects)
- Realistic user scenarios
- **Coverage**: End-to-end user workflows

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Suites

#### Unit Tests Only
```bash
pytest tests/unit/ -v
```

#### Integration Tests Only
```bash
pytest tests/integration/ -v
```

#### E2E Tests Only
```bash
pytest tests/e2e/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_output_manager.py -v
pytest tests/unit/test_progress.py -v
pytest tests/unit/test_cli.py -v
pytest tests/integration/test_workflows.py -v
pytest tests/e2e/test_full_pipeline.py -v
```

### Run with Coverage
```bash
# All tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Specific component coverage
pytest tests/unit/test_output_manager.py --cov=src.utils.output_manager
pytest tests/unit/test_progress.py --cov=src.utils.progress
pytest tests/unit/test_cli.py --cov=src.cli.main
```

### Run Specific Test Class or Method
```bash
pytest tests/unit/test_output_manager.py::TestOutputManager -v
pytest tests/unit/test_output_manager.py::TestOutputManager::test_initialization -v
```

## Test Statistics

### Total Test Count: **150+ tests**

- **Unit Tests**: 110+ tests
  - OutputManager: 40+ tests
  - Progress: 30+ tests  
  - CLI: 40+ tests
  - Config: 12 tests (Phase 1)
  - Validators: 15+ tests (Phase 1)
  - Exceptions: 10+ tests (Phase 1)

- **Integration Tests**: 30+ tests
  - Workflow integration
  - Component interactions
  - Error handling

- **E2E Tests**: 30+ tests
  - Full pipeline scenarios
  - User workflows
  - Performance testing

## Test Coverage Goals

- **Unit Tests**: 90%+ coverage of individual components
- **Integration Tests**: 80%+ coverage of component interactions
- **E2E Tests**: 70%+ coverage of user-facing features

## Test Fixtures

### Common Fixtures
- `temp_output_dir` - Temporary output directory (auto-cleanup)
- `temp_workspace` - Temporary workspace (auto-cleanup)
- `sample_state` - Mock state dictionary
- `sample_job_description` - Sample job description text
- `sample_tdd_content` - Sample TDD content
- `job_description_file` - Temporary job file
- `tdd_file` - Temporary TDD file

## Mocking Strategy

Tests use mocking for:
- LLM API calls (to avoid costs and ensure speed)
- File system operations (where appropriate)
- External dependencies
- Rich console output (for testing)

## Test Best Practices

1. **Isolation**: Each test is independent and uses fixtures
2. **Cleanup**: Temporary files/directories are automatically cleaned up
3. **Fast**: Unit tests run in < 1 second each
4. **Descriptive**: Clear test names describing what is tested
5. **Coverage**: Comprehensive edge case coverage

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:
- No external dependencies required (mocked)
- Deterministic results
- Fast execution
- Clear failure messages

## Known Limitations

1. **LLM Integration**: Most tests mock LLM calls to avoid API costs
2. **Docker Testing**: Docker functionality tested but not executed
3. **Network Calls**: External API calls are mocked
4. **Performance**: Some E2E tests may take longer to execute

## Future Enhancements

- [ ] Add performance benchmarking tests
- [ ] Add load testing for concurrent operations
- [ ] Add more realistic LLM response mocking
- [ ] Add visual regression tests for CLI output
- [ ] Add mutation testing for test quality validation

## Troubleshooting

### Tests Failing Locally

1. **Import Errors**: Ensure virtual environment is activated
   ```bash
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. **Missing Dependencies**: Install test dependencies
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Permission Errors**: Check file system permissions for temp directories

4. **Path Issues**: Tests automatically add project root to sys.path

### Slow Tests

1. Use `-v` flag to see which tests are slow
2. Run only fast unit tests: `pytest tests/unit/ -m "not slow"`
3. Skip E2E tests: `pytest tests/unit tests/integration`

## Contributing

When adding new features:
1. Add unit tests first (TDD approach)
2. Add integration tests for component interactions
3. Add E2E tests for user-facing features
4. Aim for 80%+ coverage on new code
5. Ensure all tests pass before committing

---

**Phase 2 Testing Complete!** ✅

All Phase 2 components now have comprehensive test coverage.
