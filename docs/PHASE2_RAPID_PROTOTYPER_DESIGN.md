# Phase 2: The "Rapid Prototyper" - Design Document

## Overview

Phase 2 transforms the **dev_team agent** from generating conceptual code descriptions (markdown with code blocks) into a **Rapid Prototyper** that generates actual, commit-ready code files. It bridges Phase 1 (Architect TDDs) with working code that can be immediately tested and demonstrated to clients.

## Problem Statement

### Current Limitations
The existing `dev_team` agent (as of Phase 1):
- **Input**: Simple feature request string
- **Output**: 3 markdown files with embedded code blocks
- **Files**: `frontend_implementation.md`, `backend_implementation.md`, `integration_review.md`
- **Code**: Descriptions of what should be built, not actual working code
- **Structure**: No project scaffolding, config files, or proper file organization

### What Freelancers Need
To win jobs, freelancers need to submit:
1. **Working MVP** - Not documentation, but actual code
2. **Proper structure** - Real project with dependencies, configs
3. **Runnable demo** - Something clients can test immediately
4. **Git repository** - Ready to clone and run

## Goals

###Primary Goals
1. **Accept TDD Input** - Use Phase 1 output as blueprint
2. **Generate Actual Files** - Create `.py`, `.tsx`, `.sql`, `.json`, etc.
3. **Project Scaffolding** - Complete project structure with configs
4. **Syntax Validation** - Ensure code is syntactically correct
5. **Git-Ready Output** - Formatted, organized, ready to commit

### Secondary Goals
1. **Incremental Implementation** - Support phased development
2. **Technology Agnostic** - Handle various tech stacks
3. **Testing Scaffolds** - Generate test file templates
4. **Documentation** - Auto-generate README, setup instructions

## Architecture

### Enhanced Workflow

```
INPUT: TDD from Phase 1 OR Feature Description
           ↓
[TDD Parser] (NEW)
  - Extract: features, tech stack, API spec, data model
  - Output: Structured requirements
           ↓
[Tech Lead Dispatcher]
  - Use TDD context for decomposition
  - Create frontend/backend tasks
           ↓
[Frontend Developer] ← Parallel → [Backend Developer]
  - Generate code with file markers
  - Query specialized RAG collections
           ↓
[Code Extractor] (NEW)
  - Parse code blocks from LLM output
  - Organize into file structure
  - Extract imports and dependencies
           ↓
[Scaffolder] (NEW)
  - Generate package.json / pyproject.toml
  - Create docker-compose.yml
  - Generate .env.example
  - Create README.md
           ↓
[Code Validator] (NEW)
  - Validate Python syntax (compile())
  - Validate JS/TS syntax (node --check)
  - Check import consistency
           ↓
[Integration Reviewer]
  - Validate API consistency
  - Check data model alignment
           ↓
[File Writer] (NEW)
  - Create directory structure
  - Write files with proper formatting
  - Apply code formatters (black, prettier)
  - Generate .gitignore
           ↓
OUTPUT: Complete project directory ready for git commit
```

### New Components

#### 1. TDD Parser (`src/agents/dev_team/parsers.py`) ✅ Created
**Purpose**: Extract actionable information from Phase 1 TDD documents

**Functions**:
- `parse_tdd_sections()` - Split TDD into sections
- `extract_technology_stack()` - Get tech stack recommendations
- `extract_api_endpoints()` - Parse API design section
- `extract_data_model()` - Get entity definitions
- `extract_features_to_implement()` - Get prioritized features
- `extract_security_requirements()` - Get security specs
- `parse_tdd_to_state()` - Convert TDD to dev_team state

**Output**: Structured dict ready for state initialization

#### 2. Code Generator (`src/agents/dev_team/code_generator.py`) ✅ Created
**Purpose**: Extract and organize code from LLM output

**Functions**:
- `extract_code_blocks()` - Find ```language blocks
- `extract_file_structure()` - Parse file path markers
- `validate_code_syntax()` - Check syntax by language
- `format_code()` - Apply black/prettier formatting
- `generate_gitignore()` - Create .gitignore from tech stack
- `generate_readme()` - Create README.md
- `extract_and_organize_code()` - Full extraction pipeline

**Output**: `Dict[filepath, content]`

#### 3. File Writer Node (To Implement)
**Purpose**: Write generated code to disk

**Responsibilities**:
- Create directory structure
- Write files with UTF-8 encoding
- Apply formatting if formatters available
- Set file permissions
- Create .gitignore
- Initialize git repository (optional)

**Output State**:
- `generated_files`: List of created file paths
- `files_written`: Count of files
- `output_directory`: Root directory path

#### 4. Scaffolder Node (To Implement)
**Purpose**: Generate project boilerplate

**Generates**:
- `package.json` (Node.js projects)
- `pyproject.toml` or `requirements.txt` (Python)
- `docker-compose.yml`
- `.env.example`
- `README.md` with setup instructions
- `.gitignore`
- `Dockerfile` (if Docker in tech stack)
- `pytest.ini`, `jest.config.js` (test configs)

#### 5. Code Validator Node (To Implement)
**Purpose**: Validate generated code quality

**Checks**:
- **Syntax**: Compile Python, check JS/TS with node
- **Imports**: Verify imports resolve within project
- **Consistency**: API endpoints match frontend calls
- **Standards**: Code follows conventions

**Output**:
- `validation_results`: Dict[filepath, is_valid]
- `validation_errors`: Dict[filepath, errors]

## Enhanced State Definition ✅ Completed

Added fields to `DevTeamState`:

### TDD Input Fields
```python
tdd_content: Optional[str]  # Full TDD markdown
tdd_parsed: Optional[bool]
project_metadata: Optional[Dict[str, str]]
tech_stack: Optional[Dict[str, List[str]]]
features_to_implement: Optional[List[Dict[str, str]]]
api_specification: Optional[Dict[str, Any]]
data_model: Optional[Dict[str, Dict[str, str]]]
security_requirements: Optional[List[str]]
implementation_phase: Optional[int]  # 1, 2, or 3
```

### File Generation Fields
```python
frontend_files: Optional[Dict[str, str]]  # filepath -> content
backend_files: Optional[Dict[str, str]]
config_files: Optional[Dict[str, str]]
database_files: Optional[Dict[str, str]]
test_files: Optional[Dict[str, str]]
generated_files: Optional[List[str]]
```

### Validation Fields
```python
validation_results: Optional[Dict[str, bool]]
validation_errors: Optional[Dict[str, List[str]]]
```

### Output Metadata
```python
output_directory: Optional[str]
files_written: Optional[int]
```

## Implementation Plan

### Phase 2A: Core Infrastructure ✅ Completed
- [x] Create `parsers.py` with TDD parsing utilities
- [x] Create `code_generator.py` with code extraction
- [x] Enhance `state.py` with new fields

### Phase 2B: Graph Enhancements (In Progress)
- [ ] Add `parse_tdd` node to graph
- [ ] Enhance `tech_lead_dispatcher` to use TDD context
- [ ] Modify `frontend_developer` to mark file paths
- [ ] Modify `backend_developer` to mark file paths
- [ ] Add `extract_code` node after specialists
- [ ] Add `generate_scaffolding` node
- [ ] Add `validate_code` node
- [ ] Add `write_files` node

### Phase 2C: CLI Integration
- [ ] Add `--tdd-file` flag to `dev_team.py`
- [ ] Add `--output-dir` flag
- [ ] Add `--phase` flag (1, 2, or 3)
- [ ] Add `--mode prototyper` to `src/main.py`
- [ ] Update help text and examples

### Phase 2D: Testing & Documentation
- [ ] Create example TDD → code workflow
- [ ] Test with sample job description from Phase 1
- [ ] Document usage in PHASE2_RAPID_PROTOTYPER.md
- [ ] Create quick start guide
- [ ] Add to main README

## Usage Examples

### Example 1: From TDD File

```bash
# Step 1: Generate TDD from job description (Phase 1)
python architect.py --job-description --goal "$(cat job.txt)" --no-interactive > design.md

# Step 2: Generate code from TDD (Phase 2)
python dev_team.py --tdd-file design.md --output-dir ./prototype --phase 1

# Output: ./prototype/ with complete project structure
```

### Example 2: Direct Feature (Backward Compatible)

```bash
# Original workflow still works
python dev_team.py --feature "Build user authentication with JWT"

# Outputs: frontend_implementation.md, backend_implementation.md, integration_review.md
```

### Example 3: Via Unified CLI

```bash
# New unified interface
python src/main.py --mode prototyper \
  --tdd-file design.md \
  --output ./mvp \
  --phase 1
```

### Example 4: Incremental Development

```bash
# Phase 1: Core MVP
python dev_team.py --tdd-file design.md --output ./app --phase 1

# Phase 2: Extended features
python dev_team.py --tdd-file design.md --output ./app --phase 2

# Phase 3: Polish and optimization
python dev_team.py --tdd-file design.md --output ./app --phase 3
```

## Expected Output Structure

For a typical full-stack application:

```
project/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Settings
│   │   ├── database.py             # DB setup
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── post.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   └── users.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── auth_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── jwt.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   └── test_users.py
│   ├── alembic/                    # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── index.tsx
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   └── UserProfile.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useApi.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── auth.ts
│   │   └── styles/
│   │       └── global.css
│   ├── public/
│   │   └── index.html
│   ├── tests/
│   │   └── components.test.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── .env.example
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── Makefile                        # Convenience commands
```

## Technical Challenges & Solutions

### Challenge 1: LLM Output Parsing
**Problem**: LLMs generate code in various formats (with or without file markers)
**Solution**: Multiple extraction strategies:
1. Look for explicit file markers (`File: path`)
2. Extract code blocks by language
3. Infer file names from code content (class/function names)
4. Use sensible defaults based on framework conventions

### Challenge 2: Import Resolution
**Problem**: Generated files may have incorrect or missing imports
**Solution**:
1. Post-process to add common imports (React, FastAPI, etc.)
2. Validate imports within project structure
3. Use LLM with RAG context showing import patterns
4. Flag unresolved imports for manual review

### Challenge 3: Code Quality
**Problem**: Generated code may not be syntactically valid
**Solution**:
1. Syntax validation before writing
2. Optionally run formatters (black, prettier)
3. Track validation results in state
4. Provide clear error messages for fixing

### Challenge 4: Project Structure Variance
**Problem**: Different frameworks have different conventions
**Solution**:
1. Detect framework from tech stack
2. Use template structures per framework
3. Query RAG for framework-specific patterns
4. Allow custom structure via config

### Challenge 5: Dependency Management
**Problem**: Need to generate accurate dependency lists
**Solution**:
1. Extract imports from all generated files
2. Map imports to package names (e.g., `fastapi` package for `from fastapi import`)
3. Query common dependency versions
4. Generate `requirements.txt` or `package.json`

## Success Metrics

### Functionality
- [ ] Accepts TDD files and parses correctly
- [ ] Generates syntactically valid Python code
- [ ] Generates syntactically valid TypeScript/JavaScript code
- [ ] Creates proper directory structure
- [ ] Generates working `requirements.txt` / `package.json`
- [ ] Creates functional `docker-compose.yml`
- [ ] Generates helpful README.md

### Quality
- [ ] 90%+ syntax validation pass rate
- [ ] Generated code follows language conventions
- [ ] Imports resolve correctly
- [ ] API endpoints consistent between frontend/backend
- [ ] Database models match API schemas

### Usability
- [ ] Can run `npm install` / `pip install` successfully
- [ ] Can start dev servers without errors
- [ ] Basic functionality works (e.g., API endpoints respond)
- [ ] Docker containers build successfully
- [ ] README instructions are accurate

### Performance
- [ ] Generates simple project in < 2 minutes
- [ ] Handles complex TDDs (20+ features)
- [ ] Works with various tech stacks
- [ ] Supports incremental generation (phases)

## Future Enhancements (Phase 3+)

### Phase 3: The "Full Stack Agent"
- Real-time collaboration between multiple specialist agents
- Automated testing and bug fixes
- Performance optimization suggestions
- Security vulnerability scanning
- Code review with improvement suggestions

### Beyond Phase 3
- Integration with CI/CD pipelines
- Automatic deployment to staging environments
- Client feedback integration loop
- Code evolution and refactoring
- Multi-language support expansion

## Risk Mitigation

### Risk: Generated Code Doesn't Work
**Mitigation**:
- Syntax validation before writing files
- Test file generation with basic assertions
- Clear documentation of what's generated vs. needs manual work
- Provide troubleshooting guide

### Risk: LLM Hallucinations
**Mitigation**:
- Use temperature 0.1-0.3 for code generation
- Validate against RAG-retrieved patterns
- Structured output with Pydantic models
- Multiple validation layers

### Risk: Dependency Conflicts
**Mitigation**:
- Use well-known, stable package versions
- Generate lock files (package-lock.json, poetry.lock)
- Include version constraints
- Provide upgrade instructions

### Risk: Security Vulnerabilities
**Mitigation**:
- Generate secure defaults (password hashing, SQL injection prevention)
- Include security best practices from TDD
- Add security-focused comments in code
- Suggest security scanning tools in README

## Integration with Existing System

### Backward Compatibility
- Original `dev_team.py` workflow still works
- New functionality is opt-in via `--tdd-file` flag
- Existing state fields maintained
- New fields are Optional, defaulting to None

### Unified CLI
```python
# src/main.py additions
python src/main.py --mode prototyper --tdd-file design.md --output ./code
```

### Phase 1 → Phase 2 Pipeline
```bash
# Combined workflow script
./scripts/instant_mvp.sh job_description.txt

# Internally runs:
# 1. python architect.py --job-description --goal "$(cat job_description.txt)" > tdd.md
# 2. python dev_team.py --tdd-file tdd.md --output ./mvp --phase 1
# 3. cd mvp && docker-compose up
```

## Documentation Requirements

### For Developers
- Code comments explaining each node
- Type hints for all functions
- Docstrings with usage examples
- Architecture diagrams

### For Users
- Quick start guide (5-minute MVP)
- Detailed usage guide
- Troubleshooting common issues
- Example workflows
- Tech stack compatibility matrix

### For Contributors
- Design principles
- Adding new language support
- Adding new framework templates
- Testing guidelines

## Timeline Estimate

- **Week 1**: Core infrastructure (parsers, code generator) ✅ Done
- **Week 2**: Graph enhancement (new nodes, modified workflow)
- **Week 3**: File writing, scaffolding, validation
- **Week 4**: CLI integration, testing, bug fixes
- **Week 5**: Documentation, examples, polish

## Conclusion

Phase 2 transforms the Second Brain Agent from a design tool into a **practical MVP generator** for freelancers. By accepting Phase 1 TDDs and generating actual working code, it provides:

1. **Competitive Advantage**: Submit working prototypes, not just proposals
2. **Time Savings**: Go from job description to demo in < 5 minutes
3. **Professional Quality**: Proper structure, formatting, best practices
4. **Client Confidence**: Show you can deliver before getting hired

The implementation balances ambition with pragmatism - start with core functionality that works, then iterate toward the full vision.

---

**Next Steps**: Proceed with Phase 2B (Graph Enhancements) to create a working prototype.