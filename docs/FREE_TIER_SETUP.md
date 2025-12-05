# Free Tier & Low-Cost Setup Guide

This guide helps you run the MVP Generator with **minimal or zero cost** using free tiers and local models.

## Goal: Zero to Minimal Cost

Perfect for:
- Testing projects before bidding
- Personal projects
- Learning and experimentation
- Avoiding upfront costs for uncertain projects

---

## Option 1: Fully Free Setup (Recommended for You!)

### Using Ollama (100% Free, Local)

**Advantages:**
- Completely free - no API keys needed
- No rate limits
- Works offline
- Privacy - your data never leaves your machine
- Unlimited generations

**Disadvantages:**
- Requires ~8GB RAM and ~4GB disk space
- Slower than cloud APIs (but acceptable)
- Lower quality than GPT-4/Claude (but good enough for MVPs)

### Installation Steps

#### 1. Install Ollama

**Windows:**
```bash
# Download from: https://ollama.ai/download
# Run the installer
```

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### 2. Pull Recommended Models

```bash
# Best for code generation (3.8GB)
ollama pull qwen2.5-coder:7b

# Alternative: Smaller but faster (1.9GB)
ollama pull qwen2.5-coder:3b

# For reasoning/planning (4.7GB)
ollama pull llama3.2:latest

# Verify installation
ollama list
```

#### 3. Test Models

```bash
# Test code generation
ollama run qwen2.5-coder:7b "Write a Python hello world function"

# Test reasoning
ollama run llama3.2 "Explain how authentication works"
```

#### 4. Configure Second Brain Agent

Update your `.env`:
```bash
# Use Ollama as primary (FREE!)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Budget mode - use smallest models
BUDGET_MODE=true
OLLAMA_PARSING_MODEL=qwen2.5-coder:3b
OLLAMA_REASONING_MODEL=llama3.2:latest
OLLAMA_CODING_MODEL=qwen2.5-coder:7b
OLLAMA_REVIEW_MODEL=qwen2.5-coder:3b

# Enable caching to speed up repeated queries
ENABLE_RESPONSE_CACHE=true
CACHE_TTL_HOURS=24

# Parallel processing (faster with local models)
ENABLE_PARALLEL_PARSING=true
```

#### 5. Run the Generator

```bash
python app.py
```

**Expected Performance:**
- TDD Generation: ~2-3 minutes (vs ~30 seconds with Gemini)
- Code Generation: ~1-2 minutes (vs ~20 seconds with Gemini)
- Total: ~5-10 minutes per project

---

## Option 2: Hybrid (Mostly Free + Gemini Free Tier)

Use Ollama for bulk work + Gemini free tier for critical tasks.

### Gemini Free Tier Limits
- **60 requests per minute**
- **1,500 requests per day**
- **1 million tokens per day**

This is **MORE than enough** for MVP generation!

### Optimal Strategy

```bash
# .env configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Use Gemini ONLY for TDD generation (highest quality needed)
LLM_REASONING_PROVIDER=google
GOOGLE_API_KEY=your_free_tier_key

# Ollama for everything else (FREE!)
OLLAMA_PARSING_MODEL=qwen2.5-coder:3b
OLLAMA_CODING_MODEL=qwen2.5-coder:7b
OLLAMA_REVIEW_MODEL=qwen2.5-coder:3b

# Budget mode
BUDGET_MODE=true
ENABLE_RESPONSE_CACHE=true
```

**Cost per generation:**
- Ollama (parsing, code, review): **$0.00**
- Gemini free tier (TDD only): **$0.00** (within limits)
- **Total: $0.00**

**Generations per day:**
- Limited only by your compute time
- Estimate: **10-20 full projects per day** (if you have time!)

---

## Option 3: Ultra Budget Mode (Smallest Models)

Maximize speed, minimize cost/resource usage.

### Recommended Models

```bash
# Install smallest viable models
ollama pull qwen2.5-coder:1.5b    # Tiny! 934MB
ollama pull llama3.2:1b           # Ultra small! 1.3GB
ollama pull phi3:mini             # Microsoft's tiny model, 2.3GB
```

### Configuration

```bash
# .env
LLM_PROVIDER=ollama
BUDGET_MODE=ultra

# Use tiniest models
OLLAMA_PARSING_MODEL=phi3:mini
OLLAMA_REASONING_MODEL=phi3:mini
OLLAMA_CODING_MODEL=qwen2.5-coder:1.5b
OLLAMA_REVIEW_MODEL=phi3:mini

# Aggressive caching
ENABLE_RESPONSE_CACHE=true
CACHE_TTL_HOURS=72

# Fast parallel processing
ENABLE_PARALLEL_PARSING=true
```

**Pros:**
- Fastest local generation
- Minimal disk/RAM usage (~4GB total)
- Zero cost

**Cons:**
- Lower code quality (but still usable)
- May need manual fixes

---

## Cost Comparison

### Per MVP Generation

| Strategy | Cost | Time | Quality | Best For |
|----------|------|------|---------|----------|
| **Ollama Only** | $0.00 | 5-10min | Good | Personal projects, testing |
| **Hybrid (Ollama + Gemini Free)** | $0.00 | 3-5min | Very Good | Most projects |
| **Ultra Budget (Tiny Models)** | $0.00 | 2-4min | Fair | Quick prototypes |
| Gemini Paid Tier | $0.02 | 2-3min | Excellent | Client projects (after winning) |
| Claude Paid | $0.40 | 2min | Excellent | Premium projects only |

### Monthly Costs

| Usage | Ollama Only | Hybrid Free | Gemini Paid | Claude Paid |
|-------|-------------|-------------|-------------|-------------|
| 10 MVPs/month | $0 | $0 | $0.20 | $4.00 |
| 50 MVPs/month | $0 | $0* | $1.00 | $20.00 |
| 100 MVPs/month | $0 | $5** | $2.00 | $40.00 |

\* Within Gemini free tier limits
\** Some paid calls if exceeding free tier

---

## Quick Start (Free Setup)

### 1. Install Ollama
```bash
# Download and install from https://ollama.ai
```

### 2. Pull Models
```bash
ollama pull qwen2.5-coder:7b
ollama pull llama3.2:latest
```

### 3. Update Configuration
```bash
# Copy and edit .env
cp .env.example .env

# Update with:
LLM_PROVIDER=ollama
BUDGET_MODE=true
ENABLE_RESPONSE_CACHE=true
```

### 4. Run!
```bash
python app.py
```

---

## Advanced: Custom Model Wrappers

You mentioned wanting to create wrappers for code generation. Here's how:

### Custom Free API Wrapper

If you have access to other free APIs (HuggingFace, etc.):

```python
# src/core/custom_wrapper.py
from langchain_core.language_models import BaseChatModel

class FreeAPIWrapper(BaseChatModel):
    """Wrapper for your custom free API"""

    def __init__(self, api_url: str, api_key: str = None):
        self.api_url = api_url
        self.api_key = api_key

    def _generate(self, messages, stop=None, **kwargs):
        # Your custom API call here
        pass
```

Then use it:
```python
# In llm_factory.py
from src.core.custom_wrapper import FreeAPIWrapper

if provider == "custom":
    return FreeAPIWrapper(api_url=os.getenv("CUSTOM_API_URL"))
```

---

## Cost-Saving Tips

### 1. **Use Response Caching**
```bash
ENABLE_RESPONSE_CACHE=true
CACHE_TTL_HOURS=24
```
- Saves ~30% of repeated calls
- Speeds up regenerations

### 2. **Batch Similar Projects**
Generate multiple similar MVPs in one session:
- Models stay loaded in memory
- Faster subsequent generations
- No repeated startup time

### 3. **Use Gemini Free Tier Strategically**
Only for the most important task (TDD generation):
```bash
LLM_PROVIDER=ollama
LLM_REASONING_PROVIDER=google  # Only for TDD
```

### 4. **Smaller Context Windows**
Reduce TDD size to save tokens:
```bash
MAX_TDD_SIZE=50000  # Instead of 500000
```

### 5. **Monitor Your Usage**
Track API calls per project to stay within free tiers.

---

## Scaling Strategy

### Phase 1: Testing (0 Projects Won)
**Setup:** Ollama only
**Cost:** $0/month
**Purpose:** Test and learn

### Phase 2: Bidding (1-5 Projects Won)
**Setup:** Hybrid (Ollama + Gemini Free)
**Cost:** $0/month
**Purpose:** Create professional proposals

### Phase 3: Growing (5+ Projects Won)
**Setup:** Gemini Paid for all
**Cost:** $10-20/month
**Purpose:** Fast turnaround, high quality

### Phase 4: Established (10+ Projects/month)
**Setup:** Claude for premium, Gemini for standard
**Cost:** $50-100/month
**Purpose:** Best quality for high-value clients

---

## Troubleshooting Free Setup

### Issue: "Ollama not found"
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
# Windows: Restart from system tray
# Linux/Mac: sudo systemctl restart ollama
```

### Issue: "Model too slow"
```bash
# Use smaller models
ollama pull qwen2.5-coder:3b  # Instead of 7b
ollama pull phi3:mini          # Very fast
```

### Issue: "Out of memory"
```bash
# Use smaller models or close other apps
# Minimum: 8GB RAM
# Recommended: 16GB RAM
```

### Issue: "Low quality output"
```bash
# Upgrade to 7b models:
ollama pull qwen2.5-coder:7b

# Or use Gemini free tier for critical tasks:
LLM_REASONING_PROVIDER=google
GOOGLE_API_KEY=your_key
```

---

## Recommended Model Sizes

### For Your Use Case (Free Tier, Testing Projects)

**Best Balance:**
```
Parsing:   qwen2.5-coder:3b  (fast, small, good enough)
Reasoning: llama3.2:latest   (good planning/TDD)
Coding:    qwen2.5-coder:7b  (best code quality)
Review:    qwen2.5-coder:3b  (fast validation)
```

**Total Disk:** ~10GB
**Total RAM:** ~8GB during generation
**Cost:** $0

---

## Summary: Your Optimal Setup

Based on your requirements:

```bash
# .env configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Budget mode with good quality
BUDGET_MODE=true
OLLAMA_PARSING_MODEL=qwen2.5-coder:3b
OLLAMA_REASONING_MODEL=llama3.2:latest
OLLAMA_CODING_MODEL=qwen2.5-coder:7b
OLLAMA_REVIEW_MODEL=qwen2.5-coder:3b

# Optional: Use Gemini free tier for TDD only
LLM_REASONING_PROVIDER=google
GOOGLE_API_KEY=your_free_tier_key

# Speed & cost optimizations
ENABLE_RESPONSE_CACHE=true
ENABLE_PARALLEL_PARSING=true
CACHE_TTL_HOURS=24
```

**Result:**
- Zero or near-zero cost
- Good quality MVPs
- Fast enough (5-10 min per project)
- No API limits
- Perfect for testing projects before bidding

---

## Next Steps

1. **Install Ollama** (5 minutes)
2. **Pull recommended models** (10 minutes download)
3. **Update .env** (1 minute)
4. **Generate your first free MVP!** (5 minutes)

Total setup time: **~20 minutes**
Total cost: **$0** 🎉