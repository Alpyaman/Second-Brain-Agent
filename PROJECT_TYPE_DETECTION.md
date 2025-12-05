# Project Type Detection - Implementation Summary

## What's Been Implemented

### 1. Project Type Detection (`src/agents/architect/graph.py`)
- Added `detect_project_type()` function that analyzes job descriptions
- Detects 5 project types:
  - `web_app` - Full-stack web applications
  - `script` - Python automation scripts
  - `notebook` - Data analysis Jupyter notebooks
  - `library` - Python packages/libraries
  - `api` - REST API/backend services only
  - `unknown` - Default fallback

### 2. TDD Size Limits (`src/agents/architect/graph.py`)
- Added 500KB (500,000 chars) hard limit to TDD generation
- Added repetition detection (checks for duplicate paragraphs)
- Added warning messages when truncation occurs
- Prevents 1.8MB monster TDDs

### 3. Project Type-Aware TDD Generation
- Architect prompt adjusts based on detected project type
- For scripts: Focuses on standalone Python files, no web app structure
- For notebooks: Emphasizes Jupyter notebooks, data analysis
- For APIs: Backend-only, no frontend
- For web apps: Standard full-stack approach

### 4. State Updates
- Added `project_type` field to `ArchitectState`
- Added `project_type` field to `DevTeamState`
- Project type flows from architect → dev_team

### 5. Backend Extraction Debugging
- Enhanced debugging in `extract_code_node()`
- Shows preview of backend code
- Analyzes why extraction fails (missing file paths, formatting issues)

## Still TODO

### 1. Feature Extraction Improvement
- Need to improve `extract_features_to_implement()` to be context-aware
- Should check extracted features against original job description
- Current issue: Extracts "User Registration, Login" for CRM script project

### 2. Script/Notebook Code Generation
- Need alternative code generation path for non-web-app projects
- For scripts: Generate Python `.py` files directly (no frontend/backend split)
- For notebooks: Generate `.ipynb` files with analysis cells
- Currently still tries to generate web app structure

### 3. Tech Lead Adjustment
- Tech Lead should not create frontend/backend tasks for script projects
- Should create script-specific tasks instead

## Testing

To test the improvements:

1. **Test with CRM script job description:**
   ```bash
   python app.py
   # Paste the CRM automation job description
   ```

2. **Expected behavior:**
   - TDD size < 500KB (not 1.8MB)
   - Project type detected as "script" or "notebook"
   - TDD focuses on Python scripts, not web app
   - Feature extraction may still need work
   - Code generation may still default to web app (needs more work)

3. **Check the output:**
   - Look for "Detected project type: script/notebook" message
   - Check TDD size is reasonable
   - Verify backend extraction debugging shows helpful info

## Next Steps

1. **Improve feature extraction** - Make it respect project type and job description
2. **Add script generation path** - Generate Python files for script projects
3. **Update Tech Lead** - Skip frontend/backend split for script projects
4. **Test and iterate** - Verify improvements with real job descriptions

## How to Verify

After running with a script job description, check:

```bash
# In the output, you should see:
"Detected project type: script"  # or notebook

# TDD size should be:
"Design v1 generated XXXXX characters."  # Should be < 500,000

# Backend extraction should show debug info:
"Backend code preview: ..."
"Found X total code blocks"
```

