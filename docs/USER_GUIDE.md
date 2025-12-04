# Second Brain Agent - Complete User Guide

**Transform job descriptions into working code in under 5 minutes!**

## Table of Contents
- [What is This?](#what-is-this)
- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Installation](#installation)
- [Phase 1: Instant Consultant](#phase-1-instant-consultant)
- [Phase 2: Rapid Prototyper](#phase-2-rapid-prototyper)
- [Complete Workflow](#complete-workflow)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)
- [FAQ](#faq)

---

## What is This?

The **Second Brain Agent** is an AI-powered tool for freelance developers that:

1. **Phase 1 (Instant Consultant)**: Transforms raw job descriptions from Upwork/Freelancer into professional **Technical Design Documents (TDDs)**
2. **Phase 2 (Rapid Prototyper)**: Transforms TDDs into **actual working code** with complete project structures

### Why Use It?

**For Freelancers:**
- ✅ Submit professional proposals with comprehensive technical designs
- ✅ Demonstrate expertise with working MVPs before getting hired
- ✅ Win more jobs with proof of capability
- ✅ Save 40-80 hours per project
- ✅ Higher rates due to demonstrated value

**What You Get:**
- Professional 13-section Technical Design Documents
- Complete project structures (frontend + backend + configs)
- Docker-ready development environments
- READMEs with setup instructions
- Proper .gitignore files
- Package management files (package.json, requirements.txt)

---

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.8+
- Ollama installed and running locally
- Git (optional, for version control)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/Second-Brain-Agent.git
cd Second-Brain-Agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Ollama
ollama serve
ollama pull llama2  # or codellama for better results

# 5. Configure (optional)
cp .env.example .env
# Edit .env if needed (defaults work fine)
```

### Your First Project (2 Minutes)

```bash
# Step 1: Generate Technical Design Document from job description
python architect.py --job-description \
  --goal "Build a REST API for a blog with posts, comments, and user authentication" \
  --no-interactive > design.md

# Step 2: Generate working code from the TDD
python dev_team.py --tdd-file design.md --output-dir ./my-blog-api

# Step 3: Check the result
cd my-blog-api
ls -la
# You'll see: backend/, frontend/, docker-compose.yml, README.md, .gitignore

# Step 4: Run it (if you have Docker)
docker-compose up
```

**That's it!** You now have a working project structure.

---

## Installation

### System Requirements

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB for Ollama models
- **OS**: Linux, macOS, or Windows (WSL recommended)

### Step-by-Step Setup

#### 1. Install Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com/download

#### 2. Pull AI Models

```bash
# Required (basic)
ollama pull llama2

# Recommended (better quality)
ollama pull codellama

# Best (if you have the resources)
ollama pull llama3
```

#### 3. Install Python Dependencies

```bash
cd Second-Brain-Agent
pip install -r requirements.txt
```

#### 4. Configure Environment (Optional)

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Ollama Configuration (defaults work fine)
OLLAMA_MODEL=llama2              # or codellama, llama3
OLLAMA_BASE_URL=http://localhost:11434

# Embeddings (local, no API key needed)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Database (auto-created)
CHROMA_DB_DIR=data/chroma_db
```

#### 5. Verify Installation

```bash
# Test Phase 1
python architect.py --help

# Test Phase 2
python dev_team.py --help

# If both show help text, you're ready!
```

---

## Phase 1: Instant Consultant

**Purpose**: Transform messy job descriptions into professional Technical Design Documents.

### Features

- **13-Section TDD**: Executive Summary, Requirements, Architecture, Tech Stack, Data Model, API Design, Code Structure, Security, Scalability, Implementation Plan, Testing, Deployment, Risks
- **Smart Parsing**: Extracts requirements from unstructured text
- **Interactive Refinement**: Iterate on designs with feedback
- **Professional Output**: Client-ready markdown documents

### Basic Usage

#### Interactive Mode (Recommended for First Time)

```bash
python architect.py --job-description
```

Then paste your job description and press **Ctrl+D** (Unix/Mac) or **Ctrl+Z** (Windows).

#### Non-Interactive Mode (Fast)

```bash
# From command line
python architect.py --job-description \
  --goal "Your job description here" \
  --no-interactive > design.md

# From file
python architect.py --job-description \
  --goal "$(cat job-posting.txt)" \
  --no-interactive > design.md
```

#### With Refinement

```bash
# Generate initial design
python architect.py --job-description \
  --goal "Build a real-time chat app with WebSockets"

# Review output, then provide feedback
# (The tool will prompt you for feedback)

# Output is saved to design_document_1.md
```

### Example Input/Output

**Input (Job Description):**
```
Looking for a Python dev to build REST API for blog platform.
Must use FastAPI, PostgreSQL. Need posts, comments, likes.
User auth with JWT. Budget $500, 2 weeks timeline.
```

**Output (Excerpt from 13-Section TDD):**
```markdown
# Technical Design Document

**Project:** Blog REST API Platform

## 1. EXECUTIVE SUMMARY

This project involves developing a RESTful API for a blog platform using
FastAPI and PostgreSQL. The system will provide user authentication via JWT
tokens and support core blogging features including posts, comments, and likes...

[... 12 more comprehensive sections ...]

## 10. IMPLEMENTATION PLAN

**Phase 1: Core Foundation (Week 1)**
- Database schema and models
- User authentication and JWT
- Basic CRUD for posts
Milestone: Users can create accounts and posts

**Phase 2: Extended Features (Week 2)**
- Comments and likes system
- API documentation
- Testing (90%+ coverage)
Milestone: Full feature set complete
```

### Output Files

- `design_document_1.md` - First version
- `design_document_2.md` - After refinement (if provided)
- etc.

---

## Phase 2: Rapid Prototyper

**Purpose**: Transform Technical Design Documents into actual working code.

### Features

- **Actual Code Files**: Generates .py, .tsx, .json files (not just descriptions)
- **Complete Structure**: backend/, frontend/, configs, Docker
- **Tech Stack Aware**: Adapts to FastAPI, Django, React, Next.js, etc.
- **Ready to Run**: Includes docker-compose.yml and setup instructions

### Basic Usage

#### From Phase 1 TDD

```bash
python dev_team.py --tdd-file design.md --output-dir ./my-project
```

#### With Specific Phase

```bash
# Phase 1: MVP (core features only)
python dev_team.py --tdd-file design.md --output-dir ./mvp --phase 1

# Phase 2: Extended features
python dev_team.py --tdd-file design.md --output-dir ./mvp --phase 2

# Phase 3: Polish and optimization
python dev_team.py --tdd-file design.md --output-dir ./mvp --phase 3
```

### Generated Project Structure

```
my-project/
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── models.py            # Database models
│   │   ├── config.py            # Settings
│   │   ├── routers/
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   └── posts.py         # Post endpoints
│   │   └── services/
│   │       └── auth_service.py  # Business logic
│   ├── tests/
│   │   └── test_auth.py
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   └── PostList.tsx
│   │   ├── pages/
│   │   │   └── DashboardPage.tsx
│   │   └── services/
│   │       └── api.ts
│   ├── package.json             # Node dependencies
│   └── Dockerfile
│
├── docker-compose.yml           # Multi-service orchestration
├── .gitignore                   # Tech stack-aware
├── README.md                    # Setup instructions
└── .env.example                 # Environment template
```

### What Gets Generated

1. **Backend Code**: Routes, models, services, business logic
2. **Frontend Code**: Components, pages, API integration
3. **Configuration**: package.json, requirements.txt, docker-compose.yml
4. **Documentation**: README with step-by-step setup
5. **Development Tools**: .gitignore, .env.example, Dockerfile

---

## Complete Workflow

### End-to-End: Job Description → Working Demo

```bash
# ============================================================
# COMPLETE FREELANCE WORKFLOW
# ============================================================

# Step 1: Copy job description from Upwork
cat > job.txt << 'EOF'
We need a task management system with:
- User accounts and authentication
- Create/edit/delete tasks
- Assign tasks to team members
- Due dates and priorities
- Email notifications
Budget: $3000, Timeline: 4 weeks
EOF

# Step 2: Generate Technical Design Document (30 seconds)
python architect.py --job-description \
  --goal "$(cat job.txt)" \
  --no-interactive > task-manager-tdd.md

# Step 3: Review and customize TDD (5 minutes)
# Edit task-manager-tdd.md if needed

# Step 4: Generate working code (2-3 minutes)
python dev_team.py \
  --tdd-file task-manager-tdd.md \
  --output-dir ./task-manager \
  --phase 1

# Step 5: Test locally (2 minutes)
cd task-manager
docker-compose up -d

# Visit:
# - Backend API: http://localhost:8000/docs
# - Frontend: http://localhost:3000

# Step 6: Create private repo and share (1 minute)
git init
git add .
git commit -m "Initial MVP for task management system"
git remote add origin https://github.com/your-username/task-manager-private.git
git push -u origin main

# Step 7: Submit proposal
# - Attach task-manager-tdd.md
# - Share read-only repo link
# - Note: "I've created a working prototype to demonstrate understanding"
```

**Total Time: Under 10 minutes from job description to demo!**

---

## Configuration

### Choosing the Right Model

| Model | Quality | Speed | RAM | Best For |
|-------|---------|-------|-----|----------|
| llama2 | Good | Fast | 4GB | Quick prototypes |
| codellama | Excellent | Medium | 7GB | Code generation |
| llama3 | Best | Slow | 8GB | Production quality |
| mistral | Great | Fast | 5GB | Balanced option |

Set in `.env`:
```bash
OLLAMA_MODEL=codellama  # Recommended for code
```

### Improving Code Quality

1. **Use Better Models**: Switch from llama2 to codellama or llama3
2. **Ingest Your Codebase** (Optional): Adds your coding style
   ```bash
   python src/ingestion/parent_child_ingestion.py --directory ./your-projects
   ```
3. **Add Preferences** (Optional): Tell it your coding style
   ```python
   from src.tools.memory import save_preference
   save_preference("style", "I always use type hints in Python")
   save_preference("testing", "I aim for 90%+ test coverage")
   ```

---

## Troubleshooting

### Issue: "Ollama connection failed"

**Solution:**
```bash
# Start Ollama
ollama serve

# In another terminal, pull model
ollama pull llama2

# Verify it's running
curl http://localhost:11434/api/tags
```

### Issue: "No code files generated"

**Possible Causes:**
1. TDD parsing failed - Check TDD format
2. LLM output was unexpected - Try a better model (codellama)
3. Tech stack not recognized - Manually specify in TDD

**Solution:**
```bash
# Use better model
OLLAMA_MODEL=codellama python dev_team.py --tdd-file design.md --output-dir ./test

# Check verbose output for errors
```

### Issue: "Generated code has syntax errors"

**Solutions:**
1. Use `codellama` instead of `llama2`
2. The code might have minor issues - they're usually easy fixes
3. Generated code is a starting point, not production-ready

### Issue: "Docker build fails"

**Solution:**
```bash
# Check if Docker is installed
docker --version

# If not using Docker, manually install deps:
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

### Issue: "Frontend/Backend brains not found"

**This is OK!** The system works without them. Brain collections are optional enhancements for better code quality.

To add them (optional):
```bash
python src/ingest_expert.py --expert frontend --list
python src/ingest_expert.py --expert backend --list
```

---

## Examples

### Example 1: Simple REST API

```bash
python architect.py --job-description --no-interactive \
  --goal "Build a REST API for a library system with books, authors, and borrowing" \
  > library-api-tdd.md

python dev_team.py --tdd-file library-api-tdd.md --output-dir ./library-api

cd library-api && docker-compose up
```

### Example 2: Full-Stack Application

```bash
python architect.py --job-description --no-interactive \
  --goal "$(cat examples/sample_job_description.txt)" \
  > notification-system-tdd.md

python dev_team.py \
  --tdd-file notification-system-tdd.md \
  --output-dir ./notification-system \
  --phase 1

cd notification-system
# Review generated code
# Make any customizations
docker-compose up -d
```

### Example 3: Iterative Refinement

```bash
# Generate initial TDD
python architect.py --job-description \
  --goal "E-commerce platform with cart, checkout, payments"

# Review output, then provide feedback:
# "Add support for discount codes and gift cards"

# Generates updated design_document_2.md
# Then generate code from refined design
python dev_team.py --tdd-file design_document_2.md --output-dir ./ecommerce
```

---

## FAQ

### General Questions

**Q: Does it work without API keys?**
A: Yes! Uses local Ollama - completely free, no API keys required.

**Q: How long does it take?**
A: Phase 1 (TDD): 30-60 seconds. Phase 2 (Code): 2-3 minutes.

**Q: What tech stacks are supported?**
A: Python (FastAPI, Django), JavaScript/TypeScript (React, Next.js, Node.js), PostgreSQL, MongoDB, Redis, Docker.

**Q: Is the generated code production-ready?**
A: It's a solid MVP foundation. You'll need to review, test, and customize for production.

**Q: Can I customize the output?**
A: Yes! Edit the TDD before Phase 2, or modify generated code after.

### Phase 1 Questions

**Q: Can I use this for non-freelance projects?**
A: Absolutely! Works for any technical design needs.

**Q: Can it handle complex requirements?**
A: Yes, it can handle complex multi-service architectures.

**Q: How do I refine a design?**
A: Use interactive mode and provide feedback when prompted.

### Phase 2 Questions

**Q: Will the generated code actually run?**
A: Usually yes, but minor fixes might be needed. Use `codellama` for best results.

**Q: Can I generate different phases incrementally?**
A: Yes! Use `--phase 1`, then `--phase 2`, etc.

**Q: What if I don't use Docker?**
A: No problem! Follow the README instructions in the generated project.

**Q: Can I add my own code templates?**
A: Advanced users can modify `src/agents/dev_team/code_generator.py`.

---

## Next Steps

### For New Users
1. Complete the Quick Start guide
2. Try generating a simple project
3. Review the generated code
4. Experiment with different job descriptions

### For Active Freelancers
1. Use it on your next Upwork/Freelancer proposal
2. Customize the TDD with client-specific details
3. Use generated code as starting point
4. Track your win rate improvement

### For Advanced Users
1. Ingest your own codebase for style matching
2. Add coding preferences for consistency
3. Customize prompts in `src/agents/architect/graph.py`
4. Extend with new tech stacks

---

## Support & Resources

- **Design Documentation**: See `docs/PHASE1_INSTANT_CONSULTANT.md` and `docs/PHASE2_RAPID_PROTOTYPER_DESIGN.md`
- **Phase 1 Usage Guide**: See `docs/INSTANT_CONSULTANT_USAGE.md`
- **GitHub Issues**: Report bugs or request features
- **Example Job Description**: See `examples/sample_job_description.txt`

---

## Tips for Success

1. **Be Specific in Job Descriptions**: More details = better TDDs
2. **Use Better Models**: `codellama` > `llama2` for code quality
3. **Review Before Submitting**: Customize TDDs and code for each client
4. **Start Small**: Try simple projects first, then tackle complex ones
5. **Iterate**: Use feedback loops in Phase 1 for better results
6. **Test Generated Code**: Always test before sharing with clients
7. **Add Your Touch**: Generated code is a foundation, not the final product

---

## License & Credits

Built with:
- **LangGraph**: Workflow orchestration
- **Ollama**: Local LLM inference (free!)
- **ChromaDB**: Vector database
- **HuggingFace**: Embeddings
- **FastAPI, React**: Generated project tech stacks

---

**Ready to 10x your freelance productivity? Let's build something!** 🚀