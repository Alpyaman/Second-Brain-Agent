# Curator Agent: Automated Codebase Discovery

The **Curator Agent** is an intelligent system that automatically discovers, filters, and ingests high-quality codebases into your Second Brain's specialized knowledge collections.

## Overview

Instead of manually searching for and ingesting codebases, the Curator Agent:

1. **Generates targeted search queries** for each domain (frontend, backend, fullstack)
2. **Executes web searches** to discover GitHub repositories
3. **Uses LLM with structured output** to filter and assess quality
4. **Automatically categorizes** repositories into appropriate brain collections
5. **Triggers ingestion** for approved high-quality repositories

## Architecture

The Curator Agent implements a **2-phase auto-ingestion graph**:

### Phase 1: Discovery & Filtering (Curator)
Uses **LangGraph** with a 4-node workflow:

```
generate_queries → execute_searches → filter_categorize → ingest_repos
```

### Phase 2: Orchestrated Ingestion (Dispatcher)
The ingestion logic has been refactored into callable functions:

- **ingest_expert.py**: Refactored to return structured results instead of CLI-only operation
- **ingestion_dispatcher.py**: Provides clean API for batch repository ingestion
- **curator_graph.py**: Node 4 directly calls dispatcher functions (no subprocess)

### Node 1: Generate Search Queries
- **Manual mode** (default): Uses predefined high-quality search queries
- **Auto mode**: Uses LLM to generate custom domain-specific queries
- Output: List of targeted search queries with domain categorization

### Node 2: Execute Web Searches
- Performs web searches for each generated query
- Collects raw search results (titles, snippets, URLs)
- Note: Currently uses example data; requires search API integration for production

### Node 3: Filter & Categorize (LLM-Powered)
- **Filters** for GitHub repository URLs only
- **Assesses quality** (1-10 scale) based on:
  - Popularity indicators (stars, forks)
  - Quality signals (template, boilerplate, best practices)
  - Code quality and documentation
- **Categorizes** into domains: `frontend`, `backend`, `fullstack`, `other`
- **Extracts technologies** (React, FastAPI, TypeScript, etc.)
- **Approves for ingestion** if quality score >= 7/10

### Node 4: Ingest Repositories (Ingestion Dispatcher)
- Uses `dispatch_batch_ingestion()` to process approved repositories
- Directly calls `ingest_expert_knowledge()` (no subprocess overhead)
- Clones and ingests repositories into appropriate ChromaDB collections:
  - `frontend_brain`: Frontend repositories
  - `backend_brain`: Backend repositories
  - `fullstack_brain`: Full-stack repositories
- Returns structured results with detailed metrics:
  - Files processed
  - Chunks created
  - Vectors stored
  - Error messages (if any)

## Usage

### Quick Start

```bash
# Discovery only (no ingestion, recommended for first run)
python curator.py --discover-only

# Full workflow with ingestion (frontend + backend)
python curator.py

# Target specific domains
python curator.py --domains frontend backend

# Use LLM to generate custom queries
python curator.py --mode auto --domains backend
```

### Command-Line Options

```bash
python curator.py [OPTIONS]

Options:
  --mode {manual,auto}         Query generation mode (default: manual)
  --domains {frontend,backend,fullstack} [...]
                               Domains to search (default: frontend backend)
  --query TEXT                 Add custom search query (repeatable)
  --max-results INT            Max results per query (default: 5)
  --discover-only              Only discover, don't ingest (testing mode)
  -h, --help                   Show help message
```

### Examples

**1. Quick Frontend Discovery**
```bash
python curator.py --domains frontend --discover-only
```

**2. Backend Ingestion with Custom Query**
```bash
python curator.py --domains backend \
  --query "FastAPI authentication template site:github.com"
```

**3. LLM-Generated Queries for Full-Stack**
```bash
python curator.py --mode auto --domains fullstack
```

**4. Multiple Custom Queries**
```bash
python curator.py \
  --query "React server components site:github.com" \
  --query "Next.js 15 app router site:github.com" \
  --discover-only
```

## Predefined Search Queries

The Curator Agent includes curated search queries for each domain:

### Frontend Queries
- Next.js 14 boilerplate template
- React TypeScript starter (>1000 stars)
- shadcn/ui components
- Vercel Next.js examples
- React best practices template
- Tailwind CSS components library (>500 stars)

### Backend Queries
- FastAPI boilerplate template (>500 stars)
- Python FastAPI best practices
- Django REST framework template (>1000 stars)
- FastAPI PostgreSQL template
- Python backend architecture
- FastAPI production template

### Full-Stack Queries
- T3 stack template
- Next.js + FastAPI template
- Full-stack TypeScript template (>500 stars)
- MERN stack boilerplate
- Full-stack Python + React template

## LLM-Powered Assessment

The Curator Agent uses **structured output with Pydantic models** to ensure consistent, validated filtering:

```python
class RepositoryAssessment(BaseModel):
    url: HttpUrl
    is_relevant: bool
    quality_score: int  # 1-10
    category: Literal["frontend", "backend", "fullstack", "other"]
    target_collection: Literal["frontend_brain", "backend_brain", "fullstack_brain", "skip"]
    reasoning: str
    technologies: List[str]
```

### Quality Assessment Criteria

The LLM assesses repositories based on:

1. **Popularity Indicators**: Stars, forks, community engagement
2. **Code Quality Signals**:
   - Template/boilerplate keywords
   - Best practices mentions
   - Production-ready indicators
3. **Documentation Quality**: README, examples, guides
4. **Maintenance**: Recent activity, active contributors
5. **Relevance**: Alignment with target domain

**Approval Threshold**: Quality score >= 7/10

## Output Example

```
======================================================================
STEP 3: FILTERING & CATEGORIZING WITH LLM
======================================================================
Initializing LLM with structured output...
Analyzing results with LLM...

LLM assessed 5 repositories

Assessment Results:
----------------------------------------------------------------------

1. https://github.com/shadcn-ui/ui
   Quality: 9/10 | Category: frontend | Collection: frontend_brain
   Technologies: React, TypeScript, Radix UI, Tailwind CSS
   Reasoning: High-quality component library with excellent documentation
   and widespread adoption. Perfect for learning modern React patterns.

2. https://github.com/tiangolo/fastapi-template
   Quality: 9/10 | Category: backend | Collection: backend_brain
   Technologies: FastAPI, Python, PostgreSQL, Docker
   Reasoning: Official FastAPI template by the framework creator. Production-ready
   with CI/CD, testing, and best practices built in.

3. https://github.com/unicodeveloper/awesome-nextjs
   Quality: 6/10 | Category: other | Collection: skip
   Technologies: Next.js
   Reasoning: Curated list, not a codebase. Useful but doesn't meet criteria
   for code ingestion.

======================================================================
Summary: 2 repositories approved for ingestion
         3 repositories filtered out
======================================================================
```

## Web Search Integration

**Note**: The current implementation includes example search results for demonstration. For production use, integrate with a web search API:

### Recommended Search APIs:
1. **Google Custom Search API** (Free tier: 100 queries/day)
2. **Serper.dev** (Free tier: 1000 queries/month)
3. **Tavily API** (AI-focused search)
4. **Brave Search API**

### Integration Steps:
1. Sign up for a search API
2. Add API credentials to `.env`
3. Update `execute_web_searches()` in `src/curator_graph.py`
4. Replace example results with actual API calls

## Configuration

### Environment Variables

```bash
# Required for LLM filtering and auto mode
GOOGLE_API_KEY=your_google_api_key

# Model for LLM operations
GEMINI_MODEL=gemini-2.0-flash-exp

# Optional: Search API credentials (when integrated)
# SEARCH_API_KEY=your_search_api_key
```

### Predefined Queries Customization

Edit `PREDEFINED_QUERIES` in `src/curator_graph.py`:

```python
PREDEFINED_QUERIES = {
    "frontend": [
        "Your custom frontend query site:github.com",
        # ... more queries
    ],
    "backend": [
        "Your custom backend query site:github.com",
        # ... more queries
    ],
}
```

## Workflow State

The Curator Agent tracks state through the workflow:

```python
class CuratorState(TypedDict):
    mode: str                          # "auto" or "manual"
    domains: List[str]                 # ["frontend", "backend"]
    custom_queries: List[str]          # User-provided queries
    max_results_per_query: int         # Results limit
    search_queries: List[Dict]         # Generated queries
    raw_search_results: List[Dict]     # Search results
    assessed_repositories: List[Dict]  # LLM assessments
    approved_for_ingestion: List[Dict] # Approved repos
    ingestion_results: List[Dict]      # Ingestion outcomes
    status: str                        # Workflow status
    error: Optional[str]               # Error message
```

## Best Practices

### 1. Start with Discovery Mode
```bash
# Always test first without ingestion
python curator.py --discover-only
```

### 2. Review Before Ingesting
- Check the assessed repositories
- Verify quality scores are appropriate
- Ensure categorization is correct

### 3. Use Manual Mode for Production
```bash
# Predefined queries are tested and reliable
python curator.py --mode manual
```

### 4. Target Specific Domains
```bash
# Only discover what you need
python curator.py --domains frontend --discover-only
```

### 5. Monitor Disk Space
- Each repository can be 100MB - 1GB+
- Use `--discover-only` to preview before ingesting
- Clean up unused collections periodically

## Troubleshooting

### LangGraph Module Not Found
```bash
pip install -r requirements.txt
```

### No Search Results
- Check internet connectivity
- Verify search API credentials (when integrated)
- Try custom queries with `--query`

### Ingestion Failures
- Check git is installed: `git --version`
- Verify disk space: `df -h`
- Check repository accessibility (not private/deleted)
- Review ingestion logs for specific errors

### LLM Filtering Errors
- Verify `GOOGLE_API_KEY` is set in `.env`
- Check API quota limits
- Ensure `GEMINI_MODEL` is valid

## Future Enhancements

### Planned Features
1. **Web Search API Integration**
   - Google Custom Search
   - Serper.dev API
   - Tavily Search

2. **Advanced Filtering**
   - Language-specific filtering (Python, TypeScript, etc.)
   - Minimum stars threshold
   - Last updated date filtering
   - License filtering

3. **Scheduling**
   - Cron job support for automatic discovery
   - Weekly/monthly auto-discovery runs
   - Incremental updates for existing collections

4. **Quality Metrics**
   - GitHub API integration for accurate metrics
   - Code quality analysis (linting scores)
   - Documentation quality scoring
   - Test coverage analysis

5. **Interactive Mode**
   - Manual approval before each ingestion
   - Repository preview with LLM summary
   - Category override options

6. **Collection Management**
   - Deduplicate repositories
   - Update existing repositories
   - Remove outdated/unmaintained repos

## Ingestion Dispatcher API

The **Ingestion Dispatcher** provides a clean Python API for programmatic repository ingestion.

### Single Repository Ingestion

```python
from src.ingestion_dispatcher import dispatch_ingestion

# Ingest a single repository
result = dispatch_ingestion(
    repo_url="https://github.com/shadcn-ui/ui",
    target_collection="frontend_brain",
    verbose=True
)

# Result structure:
# {
#     'success': True,
#     'expert_type': 'frontend',
#     'collection': 'frontend_brain',
#     'repo_url': 'https://github.com/shadcn-ui/ui',
#     'files_processed': 156,
#     'chunks_created': 423,
#     'vectors_stored': 423,
#     'error': None
# }
```

### Batch Repository Ingestion

```python
from src.ingestion_dispatcher import dispatch_batch_ingestion

# Ingest multiple repositories
repositories = [
    {
        'url': 'https://github.com/shadcn-ui/ui',
        'target_collection': 'frontend_brain',
    },
    {
        'url': 'https://github.com/tiangolo/fastapi-template',
        'target_collection': 'backend_brain',
    },
]

results = dispatch_batch_ingestion(repositories, verbose=True)

# Returns list of result dictionaries
for r in results:
    if r['success']:
        print(f"✅ {r['repo_url']}: {r['vectors_stored']} vectors stored")
    else:
        print(f"❌ {r['repo_url']}: {r['error']}")
```

### Utility Functions

```python
from src.ingestion_dispatcher import (
    get_supported_expert_types,
    get_collection_for_expert_type,
)

# Get supported expert types
expert_types = get_supported_expert_types()
# Returns: ['frontend', 'backend', 'fullstack']

# Get default collection for expert type
collection = get_collection_for_expert_type('frontend')
# Returns: 'frontend_brain'
```

### Direct Function Call (Advanced)

```python
from src.ingest_expert import ingest_expert_knowledge

# Call the core ingestion function directly
result = ingest_expert_knowledge(
    expert_type='frontend',
    repo_url='https://github.com/vercel/next.js',
    collection_name='my_custom_frontend_brain',
    verbose=False  # Silent mode
)
```

## Integration with Second Brain

The Curator Agent seamlessly integrates with your existing Second Brain workflow:

### 1. Automated Knowledge Acquisition
```bash
# Run weekly to discover new high-quality codebases
python curator.py --mode manual
```

### 2. Domain-Specific Agents
```python
from src.brain import query_second_brain

# Frontend agent queries frontend_brain collection
answer = query_second_brain(
    "Show me Next.js 14 server component patterns",
    collection="frontend_brain"
)
```

### 3. Multi-Agent Development Team
```bash
# Curator feeds expert knowledge to dev team agents
python dev_team.py --use-expert-brains
```

### 4. Custom Ingestion Workflows
```python
from src.ingestion_dispatcher import dispatch_ingestion

# Build custom curation workflows
repos_to_ingest = get_my_curated_repos()  # Your custom logic
for repo in repos_to_ingest:
    result = dispatch_ingestion(repo['url'], repo['collection'])
    if not result['success']:
        log_error(result['error'])
```

## License & Credits

Part of the **Second-Brain-Agent** project.

Built with:
- **LangGraph**: Agent workflow orchestration
- **LangChain**: LLM integration and tooling
- **Google Gemini**: LLM for filtering and assessment
- **Pydantic**: Structured output validation
- **ChromaDB**: Vector storage for codebases
- **HuggingFace**: Embedding models

---

For more information, see the main [README.md](README.md)