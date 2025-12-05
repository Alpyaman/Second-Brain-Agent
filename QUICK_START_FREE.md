# 🎉 Quick Start: 100% FREE MVP Generation

Get started with **zero-cost** MVP generation in under 20 minutes!

---

## Option 1: Automated Setup (Recommended)

### Windows:
```bash
setup_free_tier.bat
```

### Linux/Mac:
```bash
./setup_free_tier.sh
```

This will:
- Check if Ollama is installed
- Download recommended models (~10GB)
- Create optimal configuration
- Test everything

**Then just run:**
```bash
python app.py
```

---

## Option 2: Manual Setup

### Step 1: Install Ollama

**Windows:** Download from https://ollama.ai/download

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Download Models

```bash
# For fast parsing (2GB)
ollama pull qwen2.5-coder:3b

# For code generation (4GB)
ollama pull qwen2.5-coder:7b

# For reasoning (2GB)
ollama pull llama3.2:latest
```

### Step 3: Configure

Copy `.env.example` to `.env` and use Example 5:

```bash
cp .env.example .env
```

Edit `.env`:
```env
LLM_PROVIDER=ollama
BUDGET_MODE=true
OLLAMA_PARSING_MODEL=qwen2.5-coder:3b
OLLAMA_REASONING_MODEL=llama3.2:latest
OLLAMA_CODING_MODEL=qwen2.5-coder:7b
OLLAMA_REVIEW_MODEL=qwen2.5-coder:3b
ENABLE_PARALLEL_PARSING=true
ENABLE_RESPONSE_CACHE=true
```

### Step 4: Run

```bash
python app.py
```

---

## 🎯 What You Get

✅ **100% FREE** - No API keys, no credit card
✅ **Unlimited** - Generate as many MVPs as you want
✅ **Offline** - Works without internet (after initial download)
✅ **Private** - Your data never leaves your machine
✅ **Fast Enough** - 5-10 minutes per MVP

---

## 💡 Bonus: Add Gemini Free Tier (Optional)

For even better quality, use Gemini's free tier for TDD generation only:

1. Get a free API key: https://makersuite.google.com/app/apikey
2. Add to `.env`:
   ```env
   LLM_REASONING_PROVIDER=google
   GOOGLE_API_KEY=your_free_key_here
   ```

This uses Ollama for everything except TDD generation (the most important task), giving you **best quality** while staying **100% free** (within Gemini's generous free tier limits).

---

## 📊 Performance Expectations

| Task | Time | Cost |
|------|------|------|
| Parse Job Description | ~10s | $0 |
| Generate TDD | ~2-3min | $0 |
| Parse TDD (parallel) | ~30s | $0 |
| Generate Code | ~1-2min | $0 |
| **Total** | **~5-10min** | **$0** |

Compare to paid setup:
- Gemini: ~3min, $0.02
- Claude: ~2min, $0.40

---

## 🆘 Troubleshooting

**"Ollama not found"**
- Install Ollama from https://ollama.ai
- Make sure it's running (check system tray/menu bar)

**"Model too slow"**
- Close other applications
- Use smaller models: `ollama pull qwen2.5-coder:1.5b`
- Your machine may need more RAM

**"Out of memory"**
- Close other applications
- Use ultra budget mode (see `.env.example` Example 6)
- Need at least 8GB RAM

**"Quality not good enough"**
- Add Gemini free tier for TDD (see bonus section above)
- Use larger models: Already using 7b for code gen
- May need paid tier for production projects

---

## 📚 More Information

- **Full Free Tier Guide:** `docs/FREE_TIER_SETUP.md`
- **Multi-Model Configuration:** `docs/MULTI_MODEL_CONFIGURATION.md`
- **Environment Variables:** `.env.example`

---

## 🚀 Ready to Generate!

```bash
# Start the server
python app.py

# Open your browser
http://localhost:8000

# Generate your first FREE MVP!
```

**Cost: $0.00** 🎉

Perfect for:
- Testing projects before bidding
- Personal projects
- Learning and experimentation
- Avoiding upfront costs

Once you win projects and have budget, you can easily upgrade to paid models for faster/better quality!