# Instant Consultant - Quick Start Guide

## What is it?

The **Instant Consultant** is an AI-powered tool that transforms raw job descriptions from platforms like Upwork or Freelancer into professional, comprehensive **Technical Design Documents (TDDs)**. Submit impressive proposals that demonstrate your expertise before even getting the job!

## Quick Start

### 1. Basic Usage

```bash
# Interactive mode - just paste your job description
python architect.py --job-description
```

Then paste the job description when prompted and press **Ctrl+D** (Unix/Mac) or **Ctrl+Z** (Windows) to finish.

### 2. From a File

```bash
# Save job description to a file
cat > job.txt
[Paste job description here, then Ctrl+D]

# Generate design
python architect.py --job-description --goal "$(cat job.txt)"
```

### 3. Try the Example

```bash
# Use the provided sample job description
python architect.py --job-description --goal "$(cat examples/sample_job_description.txt)"
```

## What You Get

A professional Technical Design Document with:

1. **Executive Summary** - Overview and business value
2. **Requirements Analysis** - Functional and non-functional requirements
3. **System Architecture** - Components, patterns, and interactions
4. **Technology Stack** - Recommended technologies with justification
5. **Data Model** - Database schema and relationships
6. **API Design** - Endpoints, authentication, security
7. **Code Structure** - Project organization and conventions
8. **Security Considerations** - Best practices and measures
9. **Scalability & Performance** - Strategies for growth
10. **Implementation Plan** - Phased timeline with milestones
11. **Testing Strategy** - Unit, integration, E2E approaches
12. **Deployment & Operations** - CI/CD, monitoring, maintenance
13. **Risks & Mitigation** - Potential issues and solutions

## Features

### ✨ Smart Parsing
Automatically extracts from messy job descriptions:
- Project title
- Key features
- Technical requirements
- Budget and timeline
- Constraints and preferences

### 🎯 Personalized
- Uses your existing codebase patterns
- Aligns with your coding preferences
- Reflects your proven architectures

### 🔄 Iterative
- Review and refine designs
- Multiple versions with history
- Interactive feedback loop

### 💾 Professional Output
- Clean markdown formatting
- Smart file naming (e.g., `TDD_Notification_System_v1.md`)
- Client-ready quality

## Workflow

```
You copy job description from Upwork
           ↓
Paste into Instant Consultant
           ↓
AI analyzes and structures requirements
           ↓
Generates professional TDD (1-2 minutes)
           ↓
Review and refine if needed
           ↓
Save as markdown file
           ↓
Submit as part of your proposal!
```

## Real Example

### Input (Job Description):
```
Need a Python dev to build REST API for blog.
Must use FastAPI, PostgreSQL, user auth.
Budget: $500, Timeline: 2 weeks.
```

### Output (Generated TDD - Excerpt):
```markdown
# Technical Design Document

**Project:** Blog REST API System

# 1. EXECUTIVE SUMMARY

This project involves developing a RESTful API for a blog platform using
modern Python technologies. The system will provide secure user
authentication and efficient content management capabilities...

# 3. SYSTEM ARCHITECTURE

Components:
- FastAPI Application Server
- PostgreSQL Database
- JWT Authentication Service
- Content Management Module
- User Management Module

[... 10 more comprehensive sections ...]

# 10. IMPLEMENTATION PLAN

Phase 1: Foundation (Week 1)
- Set up FastAPI project structure
- Configure PostgreSQL connection
- Implement user model and authentication
- Basic CRUD for users

Phase 2: Core Features (Week 1-2)
- Blog post CRUD operations
- Comment system
- Search functionality
- User permissions

Phase 3: Polish (Week 2)
- API documentation
- Testing (90%+ coverage)
- Deployment setup
- Performance optimization

Milestones:
- Day 3: Authentication working
- Day 7: Core API endpoints complete
- Day 10: Testing complete
- Day 14: Production deployment
```

## Tips for Best Results

### 1. **Provide Complete Information**
The more details in the job description, the better the TDD. Include:
- Specific features needed
- Tech stack preferences (if any)
- Performance requirements
- Timeline and budget constraints

### 2. **Ingest Your Codebase First** (Optional)
For personalized designs that match your style:
```bash
python src/ingestion/parent_child_ingestion.py --directory ./your_projects
```

### 3. **Save Your Preferences**
Use the memory tool to save coding preferences:
```python
# These get automatically applied to designs
from tools.memory import save_preference

save_preference("architecture", "I prefer microservices over monoliths")
save_preference("testing", "I always aim for 90%+ test coverage")
save_preference("style", "I use type hints in all Python code")
```

### 4. **Iterate and Refine**
After seeing the initial design:
- Ask for more technical depth in specific areas
- Request different technology choices
- Add constraints or requirements you forgot

### 5. **Use Better Models**
For higher quality output, use advanced models:
```bash
# In your .env file
OLLAMA_MODEL=codellama    # Best for code-related designs
# or
OLLAMA_MODEL=llama3       # Best for general quality
# or
OLLAMA_MODEL=mistral      # Good balance of speed/quality
```

## Common Use Cases

### Case 1: Quick Upwork Proposal
```bash
# Copy job description from Upwork
# Run in non-interactive mode
python architect.py --job-description --goal "[paste here]" --no-interactive > my_proposal.md

# Edit my_proposal.md to add personal touches
# Submit with your Upwork proposal!
```

### Case 2: Freelancer Bid
```bash
# Interactive mode for refinement
python architect.py --job-description
# [Paste job description]
# [Review initial design]
# [Provide feedback if needed]
# [Save final version]
# Attach to your Freelancer bid
```

### Case 3: Client Discovery Call Prep
```bash
# Before discovery call, generate TDD
python architect.py --job-description --goal "$(cat client_requirements.txt)"

# Use TDD to:
# - Show you've thought deeply about their needs
# - Ask intelligent follow-up questions
# - Demonstrate technical expertise
# - Provide realistic timeline estimates
```

## Customization Options

### All Available Flags

```bash
python architect.py \
  --job-description \           # Enable job description parsing
  --goal "text or $(cat file)" \ # Job description content
  --no-interactive              # Skip refinement loop
```

### Via Unified CLI

```bash
python src/main.py \
  --mode architect \
  --goal "$(cat job.txt)" \
  --output my_design.md
```

## Troubleshooting

### "No relevant code examples found"
**Not an error!** The system works without your codebase. To add personalization:
```bash
python src/ingestion/parent_child_ingestion.py --directory ./your_code
```

### Design is too generic
Try:
1. Use a better model (codellama, llama3)
2. Add more details to the job description
3. Ingest your codebase for style matching
4. Use the refinement loop to add specifics

### Ollama errors
Ensure Ollama is running:
```bash
ollama serve          # Start Ollama
ollama pull llama2    # Download model
```

### Output is cut off
Some models have context limits. Try:
1. Reduce job description length
2. Use a model with larger context window
3. Focus on specific sections in refinement

## Advanced Usage

### Batch Processing Multiple Jobs

```bash
#!/bin/bash
# Process all job descriptions in a directory

for job in jobs/*.txt; do
  echo "Processing $job..."
  python architect.py \
    --job-description \
    --goal "$(cat $job)" \
    --no-interactive > "tdds/$(basename $job .txt)_TDD.md"
done
```

### Integration with Proposal Templates

```bash
# Generate TDD
python architect.py --job-description --goal "..." --no-interactive > design.md

# Combine with your proposal template
cat proposal_header.md design.md proposal_footer.md > final_proposal.md
```

### API Integration (Future)

```python
from src.agents.architect.graph import run_architect_session

# Programmatic usage
job_description = """
[Job posting text here]
"""

result = run_architect_session(
    goal=job_description,
    is_job_description=True
)

print(result['design_document'])
```

## FAQ

**Q: Does it work without an API key?**
A: Yes! Uses local Ollama - completely free.

**Q: How long does it take?**
A: 10-60 seconds depending on model and complexity.

**Q: Can I edit the output?**
A: Absolutely! The TDD is markdown - edit as needed.

**Q: Will it match my coding style?**
A: If you ingest your codebase first, yes! Otherwise, it uses general best practices.

**Q: Does it support languages other than Python?**
A: Yes! It analyzes the job requirements and recommends appropriate tech stacks.

**Q: Can I use custom prompts?**
A: Advanced users can modify `src/agents/architect/graph.py` prompts.

**Q: Is the output copyright-free?**
A: Yes, all generated content is yours to use freely.

---

## Next Steps

1. **Try it now**: `python architect.py --job-description`
2. **Read full docs**: `docs/PHASE1_INSTANT_CONSULTANT.md`
3. **Customize**: Ingest your codebase and add preferences
4. **Win jobs**: Submit impressive proposals! 🚀

**Questions or issues?** Open an issue on GitHub or check the main README.