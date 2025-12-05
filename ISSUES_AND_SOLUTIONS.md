# Issues Found and Solutions

## Problems Identified

### 1. Wrong Project Type Detection
**Issue**: System generated auth/login web app code instead of Python scripts for CRM automation.

**Root Cause**: 
- The architect is interpreting the job description as a web application
- The feature extraction is defaulting to common web app patterns (auth, login, JWT)
- System is designed primarily for web apps (frontend + backend), not standalone scripts

**Job Description Says**:
- Python automation scripts
- JSON endpoint fetching
- CSV data analysis
- Jupyter notebook analysis
- No web app mentioned

**Solution**: 
- Need to detect project type early (web app vs scripts vs notebooks)
- Adjust architecture and code generation based on project type
- For scripts: Generate Python files directly, not API endpoints

---

### 2. TDD Size Issue (1.8MB!)
**Issue**: Technical Design Document generated is 1,831,952 characters (~1.8MB) - way too large.

**Possible Causes**:
- LLM repeating content in a loop
- TDD generation prompt causing excessive output
- No size limits in architect generation

**Impact**:
- Slows down processing
- Wastes tokens/costs
- Harder to parse and extract features

**Solution**:
- Add size limits/truncation to TDD generation
- Add checks to prevent repetition
- Monitor and log TDD sizes

---

### 3. Backend Code Not Extracted (0 files)
**Issue**: Backend code was generated (19,045 characters) but 0 files were extracted.

**Root Causes**:
- Code blocks might not have file paths
- Code extraction regex might not match the format
- Backend code format might be different than expected

**Solution** (Already Applied):
- Added debugging to show why extraction fails
- Shows code preview and code block analysis
- Will help identify the exact issue

---

### 4. Feature Extraction Wrong
**Issue**: Extracted "User Registration, User Login, JWT Token Generation" instead of:
- Promo code assignment script
- JSON endpoint fetching
- CSV analysis
- Campaign impact analysis

**Root Cause**: 
- `extract_features_to_implement()` uses LLM to extract from TDD
- If TDD contains wrong content (auth features), extraction will be wrong
- The example in the prompt shows "User Authentication" which might bias it

**Solution**:
- Improve feature extraction prompt to be more context-aware
- Check if extracted features match job description
- Fallback to job description if TDD extraction seems wrong

---

## Immediate Fixes Applied

**Added backend extraction debugging** - Will show why files aren't being extracted

## Recommended Fixes

### Priority 1: Project Type Detection
Add project type detection in the architect:

```python
def detect_project_type(job_description: str) -> str:
    """Detect if project is web app, script, notebook, or library."""
    keywords = {
        'script': ['script', 'automation', 'fetch', 'process', 'analyze data'],
        'notebook': ['jupyter', 'notebook', 'analysis', 'csv', 'data analysis'],
        'web_app': ['web app', 'website', 'frontend', 'backend', 'api', 'user interface'],
        'library': ['library', 'package', 'module', 'pip install']
    }
    # Return detected type
```

### Priority 2: Fix TDD Size
Add size limits and repetition detection:

```python
# In architect generation
if len(design_document) > 500000:  # 500KB limit
    print(" Warning: TDD is very large, truncating...")
    design_document = design_document[:500000]
```

### Priority 3: Better Feature Extraction
Improve the extraction prompt:

```python
prompt = f"""Extract implementable features from this implementation plan.
Focus ONLY on features mentioned in the original job description:
{original_job_description}

{phase_filter}

For each feature, provide:
FEATURE: Feature name
DESCRIPTION: What needs to be built
...
```

### Priority 4: Support Non-Web Projects
Create alternative code generation paths:

- **Scripts**: Generate standalone Python files, requirements.txt, README
- **Notebooks**: Generate Jupyter notebooks with analysis cells
- **Libraries**: Generate package structure with setup.py

---

## Workaround for Current Job

For the CRM automation project, the system should generate:

**Instead of**:
- Frontend components (RegistrationForm.tsx, LoginForm.tsx)
- Backend API (FastAPI routes, JWT auth)
- Database models

**Should generate**:
- `promo_code_assigner.py` - Script to fetch JSON, apply rules, assign codes
- `campaign_analyzer.py` - Script to analyze CSV data, compute metrics
- `analysis_notebook.ipynb` - Jupyter notebook for detailed analysis
- `requirements.txt` - Dependencies (pandas, requests, jupyter)
- `README.md` - Instructions for running scripts

---

## Next Steps

1. ✅ Debug backend extraction (done)
2. ⏳ Test again to see extraction debug output
3. ⏳ Implement project type detection
4. ⏳ Fix TDD size limits
5. ⏳ Improve feature extraction accuracy
6. ⏳ Add support for script/notebook projects

---

## How to Verify Fixes

After fixes, test with the same job description:
- Check TDD size < 500KB
- Verify extracted features match job description
- Confirm backend files are extracted (if web app) OR Python scripts generated (if scripts)
- Ensure output matches project type

