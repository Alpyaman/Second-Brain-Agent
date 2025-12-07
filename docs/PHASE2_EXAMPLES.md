# Phase 2 Implementation Examples

## Enhanced CLI Usage

### 1. Architect Command (Generate TDD)

**Basic usage with inline job description:**
```bash
sba architect --job "Build a REST API for blog posts with user authentication"
```

**From file:**
```bash
sba architect --job-file examples/job_description.txt --output design.md
```

**Interactive mode with refinement:**
```bash
sba architect --job-file job.txt --interactive
```

**Specify model:**
```bash
sba architect --job-file job.txt --model gemini-pro --output tdd.md
```

**Skip validation (faster):**
```bash
sba architect --job "Quick prototype" --no-validate
```

### 2. Dev Team Command (Generate Code)

**Basic usage:**
```bash
sba dev-team --tdd design.md --output ./my-project
```

**Specify frameworks:**
```bash
sba dev-team --tdd design.md \
  --framework django \
  --frontend nextjs \
  --output ./django-next-app
```

**Run specific phase:**
```bash
sba dev-team --tdd design.md --phase 1 --output ./phase1-only
```

**Without Docker:**
```bash
sba dev-team --tdd design.md --no-docker --output ./no-docker-app
```

**Skip validation:**
```bash
sba dev-team --tdd design.md --no-validate --output ./quick-gen
```

### 3. Info Commands

**Show version:**
```bash
sba version
```

**Show system information:**
```bash
sba info
```

**Get help:**
```bash
sba --help
sba architect --help
sba dev-team --help
```

## Output Manager Examples

### Using in Python

```python
from pathlib import Path
from src.utils.output_manager import OutputManager, create_project_output

# Method 1: Using OutputManager class
manager = OutputManager(base_dir=Path("./output"))

# Create project directory
project_dir = manager.create_project_dir("my-awesome-app")

# Save structured output
state = {
    'backend_code': '# Backend code here',
    'frontend_code': '// Frontend code here',
    'design_document': '# Design Document',
    'backend_framework': 'fastapi',
    'frontend_framework': 'react',
    'iteration_count': 1,
}

files = manager.save_structured_output(
    project_dir,
    state,
    include_docker=True,
    include_tests=True
)

print(f"Created {len(files)} files in {project_dir}")

# Method 2: Using convenience function
project_dir = create_project_output(
    project_name="blog-api",
    state=state,
    output_dir=Path("./custom-output"),
    include_docker=True,
    include_tests=True
)
```

### Project Structure Generated

```
output/
└── my-awesome-app_20241207_143022/
    ├── backend/
    │   ├── src/
    │   │   └── main.py
    │   ├── tests/
    │   │   └── test_api.py
    │   ├── requirements.txt
    │   └── Dockerfile
    ├── frontend/
    │   ├── src/
    │   │   └── App.tsx
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

## Configuration Management Examples

### Using Settings in Python

```python
from src.core.settings import settings, get_settings

# Access settings
print(f"Model: {settings.default_model}")
print(f"Output dir: {settings.output_dir}")
print(f"Max tokens: {settings.max_tokens}")

# Check API keys
if settings.has_api_key('google'):
    print("Google API key configured")

# Get model config
config = settings.get_model_config()
print(config)  # {'model': 'gemini-pro', 'max_tokens': 4096, 'temperature': 0.7}

# Save current settings
settings.save_to_env(Path(".env.backup"))

# Reload settings (if .env changed)
from src.core.settings import reload_settings
new_settings = reload_settings()
```

### Environment Variables

Create a `.env` file:

```env
# API Keys
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Model Settings
DEFAULT_MODEL=gemini-pro
MAX_TOKENS=4096
TEMPERATURE=0.7

# Paths
OUTPUT_DIR=./my-output
LOGS_DIR=./my-logs

# Generation Settings
BACKEND_FRAMEWORK=fastapi
FRONTEND_FRAMEWORK=react
INCLUDE_DOCKER=true
INCLUDE_TESTS=true

# Features
ENABLE_CACHING=true
CACHE_TTL_SECONDS=3600
LOG_LEVEL=INFO
```

## Progress Tracking Examples

### Simple Progress

```python
from src.utils.progress import ProjectProgress

progress = ProjectProgress("Generating Code")
stages = ["Parse TDD", "Backend", "Frontend", "Docker", "Finalize"]

with progress.track_generation(stages) as update:
    for stage in stages:
        update(stage)
        # ... do actual work ...
        time.sleep(1)
```

### Multi-Stage Progress

```python
from src.utils.progress import MultiStageProgress

multi = MultiStageProgress()

with multi.run():
    # Add concurrent tasks
    multi.add_task("backend", description="Backend Generation")
    multi.add_task("frontend", description="Frontend Generation")
    multi.add_task("docker", description="Docker Config")
    
    # Update tasks
    for i in range(100):
        multi.update("backend", advance=1)
        multi.update("frontend", advance=1)
        multi.update("docker", advance=1)
        time.sleep(0.1)
```

### Show Summary

```python
from src.utils.progress import show_generation_summary

show_generation_summary(
    project_name="My Project",
    components=["Backend", "Frontend", "Docker", "Tests", "Docs"],
    time_elapsed=45.3,
    files_created=23
)
```

## Complete Workflow Example

```python
from pathlib import Path
from src.agents.architect.graph import run_architect_session
from src.agents.dev_team.graph import run_dev_team_v2
from src.utils.output_manager import OutputManager
from src.utils.progress import ProjectProgress
from src.core.settings import settings

# 1. Generate TDD from job description
job_desc = Path("job.txt").read_text()

print("Generating TDD...")
architect_state = run_architect_session(
    goal=job_desc,
    is_job_description=True
)

# Save TDD
tdd_file = Path("design.md")
tdd_file.write_text(architect_state['design_document'])
print(f"TDD saved to {tdd_file}")

# 2. Generate code from TDD
print("\nGenerating code...")

progress = ProjectProgress("Code Generation")
stages = ["Parse TDD", "Backend", "Frontend", "Integration", "Output"]

with progress.track_generation(stages) as update:
    update(stages[0])
    dev_state = run_dev_team_v2(
        tdd_file=str(tdd_file),
        output_dir=str(settings.output_dir)
    )
    
    # Update progress through stages
    for stage in stages[1:]:
        update(stage)

# 3. Save structured output
print("\nSaving output...")
manager = OutputManager()
project_dir = manager.create_project_dir("my-app")
files = manager.save_structured_output(project_dir, dev_state)

print(f"\n✓ Complete! Project created at: {project_dir}")
print(f"  Files created: {len(files)}")
```

## Integration with Existing Code

### Updating architect.py

```python
# At the top of architect.py
from src.utils.progress import ProjectProgress
from src.core.settings import settings

# In interactive_mode function
progress = ProjectProgress("Generating Design")
stages = ["Analyze Job", "Generate TDD", "Review"]

with progress.track_generation(stages) as update:
    update(stages[0])
    state = run_architect_session(goal=goal, is_job_description=is_job_description)
    update(stages[1])
    # ... rest of logic ...
```

### Updating dev_team.py

```python
# At the top of dev_team.py
from src.utils.output_manager import create_project_output
from src.utils.progress import show_generation_summary
from src.core.settings import settings
import time

# In main execution
start_time = time.time()

# ... run dev team ...

# Create structured output
project_dir = create_project_output(
    project_name="generated-app",
    state=state,
    output_dir=settings.output_dir,
    include_docker=settings.include_docker,
    include_tests=settings.include_tests
)

# Show summary
elapsed = time.time() - start_time
show_generation_summary(
    project_name=project_dir.name,
    components=["Backend", "Frontend", "Docker", "Tests", "Docs"],
    time_elapsed=elapsed,
    files_created=len(list(project_dir.rglob("*.*")))
)
```

## Testing the New Features

```bash
# Install dependencies
pip install -r requirements.txt

# Test enhanced CLI
sba --help
sba version
sba info

# Test architect with progress
sba architect --job "Build a simple blog API" --output test.md

# Test dev-team with all features
sba dev-team --tdd test.md --framework fastapi --frontend react --output ./test-app

# Check generated structure
ls -la test-app/
cat test-app/README.md
cat test-app/docker-compose.yml
```

## Makefile Integration

Add to your Makefile:

```makefile
# Phase 2 Commands
.PHONY: cli-test demo-architect demo-dev

cli-test:
	sba --help
	sba version
	sba info

demo-architect:
	sba architect --job "Build a REST API for task management" --output demo-tdd.md

demo-dev:
	sba dev-team --tdd demo-tdd.md --output ./demo-project

clean-demo:
	rm -f demo-tdd.md
	rm -rf demo-project
```
