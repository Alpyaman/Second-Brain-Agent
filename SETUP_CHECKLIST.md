# Development Environment Checklist

Use this checklist to verify your development environment is properly configured.

## ✅ Initial Setup

- [ ] Python 3.8+ installed
  ```bash
  python --version
  ```

- [ ] Git repository cloned
  ```bash
  git status
  ```

- [ ] Virtual environment created
  ```bash
  ls venv/  # Should see bin/, lib/, etc.
  ```

- [ ] Virtual environment activated
  ```bash
  which python  # Should point to venv/bin/python
  ```

---

## ✅ Dependencies Installed

- [ ] Production dependencies installed
  ```bash
  pip list | grep langchain
  pip list | grep chromadb
  ```

- [ ] Development dependencies installed
  ```bash
  pip list | grep pytest
  pip list | grep black
  ```

- [ ] Pre-commit hooks installed
  ```bash
  pre-commit --version
  ```

---

## ✅ Configuration

- [ ] `.env` file created
  ```bash
  ls -la | grep .env
  ```

- [ ] API keys configured (at least one)
  ```bash
  grep "API_KEY" .env
  ```

- [ ] Required directories exist
  ```bash
  ls -d logs output src/data/chroma_db
  ```

---

## ✅ Code Quality Tools

- [ ] Black can run
  ```bash
  black --version
  ```

- [ ] isort can run
  ```bash
  isort --version
  ```

- [ ] flake8 can run
  ```bash
  flake8 --version
  ```

- [ ] pylint can run
  ```bash
  pylint --version
  ```

- [ ] mypy can run
  ```bash
  mypy --version
  ```

---

## ✅ Testing

- [ ] Pytest installed and working
  ```bash
  pytest --version
  ```

- [ ] Can run unit tests
  ```bash
  pytest tests/unit -v
  ```

- [ ] Coverage reporting works
  ```bash
  pytest --cov=src --cov-report=term-missing
  ```

---

## ✅ Make Commands

- [ ] Make is available
  ```bash
  make --version
  ```

- [ ] `make help` shows commands
  ```bash
  make help
  ```

- [ ] `make format` works
  ```bash
  make format
  ```

- [ ] `make lint` works
  ```bash
  make lint
  ```

- [ ] `make test` works
  ```bash
  make test
  ```

---

## ✅ Project Structure

- [ ] All new directories exist
  ```bash
  ls src/utils/
  ls src/constants/
  ls tests/unit/
  ls tests/integration/
  ls tests/e2e/
  ls scripts/
  ls output/
  ls logs/
  ```

- [ ] Configuration files exist
  ```bash
  ls setup.py
  ls pyproject.toml
  ls requirements-dev.txt
  ls .pre-commit-config.yaml
  ls Makefile
  ```

---

## ✅ Imports Work

- [ ] Can import utils
  ```bash
  python -c "from src.utils import setup_logger; print('OK')"
  ```

- [ ] Can import exceptions
  ```bash
  python -c "from src.utils.exceptions import SecondBrainError; print('OK')"
  ```

- [ ] Can import validators
  ```bash
  python -c "from src.utils.validators import validate_job_description; print('OK')"
  ```

- [ ] Can import constants
  ```bash
  python -c "from src.constants import AgentType; print('OK')"
  ```

---

## ✅ Application Runs

- [ ] Architect can start
  ```bash
  python architect.py --help
  ```

- [ ] Dev team can start
  ```bash
  python dev_team.py --help
  ```

- [ ] Curator can start
  ```bash
  python curator.py --help
  ```

---

## ✅ Documentation

- [ ] README.md is readable
  ```bash
  cat README.md | head -20
  ```

- [ ] CONTRIBUTING.md exists
  ```bash
  cat CONTRIBUTING.md | head -20
  ```

- [ ] QUICK_REFERENCE.md exists
  ```bash
  cat QUICK_REFERENCE.md | head -20
  ```

---

## ✅ Optional But Recommended

- [ ] IDE/Editor configured with Python extension
- [ ] Linters configured in IDE
- [ ] Auto-formatting on save enabled
- [ ] Git configured with your name and email
- [ ] SSH keys set up for GitHub

---

## 🎉 All Checks Passed?

If you've checked all the boxes above, you're ready to start developing!

### Next Steps:

1. **Read the documentation**
   ```bash
   cat CONTRIBUTING.md
   cat QUICK_REFERENCE.md
   ```

2. **Run the tests**
   ```bash
   make test
   ```

3. **Try the examples**
   ```bash
   python architect.py --help
   ```

4. **Start coding!**
   - Create a new branch: `git checkout -b feature/my-feature`
   - Make your changes
   - Run tests: `make test`
   - Format code: `make format`
   - Commit and push

---

## 🆘 Something Not Working?

### Common Fixes:

**Import errors:**
```bash
pip install -e .
```

**Pre-commit issues:**
```bash
pre-commit clean
pre-commit install
```

**Test failures:**
```bash
make install-dev
```

**Module not found:**
```bash
source venv/bin/activate  # Make sure venv is active
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Still stuck?
- Check `CONTRIBUTING.md` for detailed setup instructions
- Review `QUICK_REFERENCE.md` for common commands
- Create an issue on GitHub

---

**Last Updated**: December 2024
