# ✅ Phase 3 Analytics - Verification Checklist

Run through this checklist to verify everything is working correctly.

---

## 1. Installation Check

```bash
# Ensure package is installed
pip install -e .

# Should show sba command
sba --help
```

**Expected:** CLI help menu appears with commands including `analytics`

---

## 2. Run Tests

```bash
# Run analytics tests
pytest tests/unit/test_analytics.py -v

# Expected: All tests pass (20+)
```

**Expected Output:**
```
tests/unit/test_analytics.py::TestGenerationMetrics::test_metrics_creation PASSED
tests/unit/test_analytics.py::TestGenerationMetrics::test_metrics_to_dict PASSED
tests/unit/test_analytics.py::TestProjectAnalytics::test_initialization PASSED
...
===================== 20 passed in 0.5s =====================
```

---

## 3. Test Analytics Module Directly

```bash
# Run the module directly (has example code)
python src/utils/analytics.py
```

**Expected:** See sample analytics report printed

---

## 4. Test CLI Commands

### View Help
```bash
sba analytics --help
```

**Expected:** Help text for analytics command

### View Analytics (Empty State)
```bash
sba analytics
```

**Expected:** "No analytics data available yet." message

### Test with Sample Data

Create a test script (`test_analytics_cli.py`):
```python
from src.utils.analytics import get_analytics

analytics = get_analytics()

# Add sample data
for i in range(5):
    analytics.track_generation(
        project_name=f"test-project-{i}",
        duration_seconds=100.0 + i * 10,
        tokens_used=3000 + i * 100,
        estimated_cost=0.30 + i * 0.01,
        success=i % 2 == 0,
        project_type="rest-api" if i % 2 == 0 else "fullstack",
        framework="fastapi" if i % 2 == 0 else "react",
        cache_hits=5,
        cache_misses=3,
        llm_requests=8
    )

print("✓ Added 5 sample projects")
```

Run it:
```bash
python test_analytics_cli.py
```

Now test CLI:
```bash
# View text report
sba analytics

# View markdown
sba analytics -f markdown

# View JSON
sba analytics -f json

# View insights
sba analytics --insights
```

**Expected:** Reports showing 5 projects with statistics

---

## 5. Test Export Functionality

```bash
# Export to CSV
sba analytics -e test_metrics.csv

# Verify file created
cat test_metrics.csv  # Linux/macOS
type test_metrics.csv  # Windows

# Export to JSON
sba analytics -e test_metrics.json --export-format json

# Verify file created
cat test_metrics.json  # Linux/macOS
type test_metrics.json  # Windows
```

**Expected:** Files created with correct data

---

## 6. Test Cleanup

```bash
# This shouldn't remove anything (all data is recent)
sba analytics --clear-old 90
```

**Expected:** "No old metrics to remove" or "Removed 0 old metrics"

---

## 7. Verify File Structure

Check that these directories/files exist:
```bash
ls -la analytics/  # Linux/macOS
dir analytics\     # Windows
```

**Expected Files:**
```
analytics/
├── generation_metrics.jsonl
└── summary.json
```

---

## 8. Integration Test (Optional)

If you want to test with real workflow:

```bash
# Generate a test project (if you have a TDD file)
sba dev-team --tdd design.md --output-dir test_output

# Or use architect
sba architect --job "Build a simple REST API" -o test_design.md
```

Then check analytics:
```bash
sba analytics
```

**Expected:** Should show the new project in statistics

---

## 9. Code Quality Check

```bash
# Run linters (if configured)
black --check src/utils/analytics.py
pylint src/utils/analytics.py
mypy src/utils/analytics.py
```

**Expected:** No errors (or minor warnings)

---

## 10. Coverage Check

```bash
# Run tests with coverage
pytest tests/unit/test_analytics.py --cov=src.utils.analytics --cov-report=term-missing

# Expected: >95% coverage
```

**Expected Output:**
```
---------- coverage: platform ..., python ... -----------
Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
src/utils/analytics.py         xxx     x    95%   xxx-xxx
----------------------------------------------------------
TOTAL                          xxx     x    95%
```

---

## ✅ Checklist Summary

- [ ] Package installed successfully
- [ ] All tests pass (20+ tests)
- [ ] Module runs directly
- [ ] CLI help works
- [ ] Analytics command works (empty state)
- [ ] Sample data loads correctly
- [ ] Text report generates
- [ ] Markdown report generates
- [ ] JSON report generates
- [ ] Insights display works
- [ ] CSV export works
- [ ] JSON export works
- [ ] Cleanup command works
- [ ] Analytics files created correctly
- [ ] (Optional) Integration with real workflow works
- [ ] Code quality checks pass
- [ ] Test coverage >95%

---

## 🐛 Troubleshooting

### Issue: "sba command not found"
```bash
# Solution: Install in editable mode
pip install -e .
```

### Issue: "ModuleNotFoundError: No module named 'src'"
```bash
# Solution: Make sure you're in project root
cd /path/to/Second-Brain-Agent
pip install -e .
```

### Issue: Tests fail with import errors
```bash
# Solution: Install dev dependencies
pip install -r requirements-dev.txt
```

### Issue: "No analytics data available"
```bash
# Solution: Generate sample data first
python test_analytics_cli.py
sba analytics
```

### Issue: Permission errors with analytics directory
```bash
# Solution: Check permissions
chmod 755 analytics/
```

---

## 📊 What Success Looks Like

After verification, you should see:

1. **All tests passing** ✅
2. **CLI command working** ✅
3. **Reports generating** ✅
4. **Data persisting** ✅
5. **Exports working** ✅
6. **Insights appearing** ✅

---

## 🎉 Next Steps After Verification

1. **Clean up test data:**
   ```bash
   rm -rf analytics/  # Remove test data
   rm test_analytics_cli.py test_metrics.csv test_metrics.json
   ```

2. **Integrate into your workflow:**
   - Add tracking to `architect.py`
   - Add tracking to `dev_team.py`
   - Add tracking to agent workflows
   
3. **Start using:**
   ```bash
   # Generate real projects
   sba architect --job "..." -o design.md
   sba dev-team --tdd design.md --output-dir output/
   
   # Check analytics
   sba analytics --insights
   ```

4. **Monitor regularly:**
   ```bash
   # Weekly check
   sba analytics
   
   # Monthly export
   sba analytics -e "metrics_$(date +%Y%m).csv"
   ```

---

**Last Updated:** December 8, 2024  
**Version:** 0.1.0
