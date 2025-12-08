# Analytics Quick Reference

## Basic Usage

```bash
# View analytics
sba analytics

# View as markdown
sba analytics -f markdown

# View as JSON
sba analytics -f json

# Show cost insights
sba analytics --insights

# Export to CSV
sba analytics -e metrics.csv

# Clear old metrics (keep last 90 days)
sba analytics --clear-old 90
```

## From Python

```python
from src.utils.analytics import get_analytics

# Get global instance
analytics = get_analytics()

# Track generation
analytics.track_generation(
    project_name="my-api",
    duration_seconds=120.5,
    tokens_used=3500,
    estimated_cost=0.35,
    success=True,
    project_type="rest-api",
    framework="fastapi",
    cache_hits=5,
    cache_misses=3,
    llm_requests=8
)

# Get summary
summary = analytics.get_summary()

# Generate report
report = analytics.generate_report(format="text")

# Get insights
insights = analytics.get_cost_insights()
```

## Metrics Tracked

- Project name, timestamp
- Duration, tokens, cost
- Success/failure status
- Project type, framework
- Cache statistics
- LLM requests
- Error messages

## Reports Include

- Total projects & success rate
- Average duration, tokens, cost
- Cache hit rate
- Project type distribution
- Framework distribution
- 7-day activity summary
- Cost optimization insights
