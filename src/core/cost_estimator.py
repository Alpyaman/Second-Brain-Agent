"""
Cost Estimator for LLM API Usage

This module provides cost estimation for different AI providers and usage patterns.

Features:
- Cost estimation per task
- Monthly cost projection
- Usage tracking
- Provider cost comparison
"""

import os
from typing import Dict, Optional
from datetime import datetime
import json
from pathlib import Path


# Cost per 1M tokens (input, output) in USD
PROVIDER_COSTS = {
    "google": {
        "gemini-2.0-flash-lite": (0.05, 0.15),
        "gemini-2.5-flash-lite": (0.05, 0.15),
        "gemini-2.0-flash-thinking-exp": (0.10, 0.30),
    },
    "anthropic": {
        "claude-3-5-haiku-20241022": (1.00, 5.00),
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        "claude-3-7-sonnet-20250219": (3.00, 15.00),
    },
    "openai": {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        "o1": (15.00, 60.00),
    },
    "ollama": {
        # All Ollama models are free
        "default": (0.0, 0.0),
    }
}

# Estimated token counts per task type
TASK_TOKEN_ESTIMATES = {
    "parsing": {"input": 2000, "output": 500},
    "reasoning": {"input": 10000, "output": 5000},
    "coding": {"input": 8000, "output": 3000},
    "review": {"input": 5000, "output": 1000},
    "creative": {"input": 3000, "output": 1000},
}


class CostEstimator:
    """Estimate and track costs for LLM API usage."""

    def __init__(self, usage_log_file: str = "./usage_log.json"):
        """
        Initialize the cost estimator.

        Args:
            usage_log_file: File to store usage logs
        """
        self.usage_log_file = Path(usage_log_file)
        self.usage_log_file.parent.mkdir(parents=True, exist_ok=True)

    def estimate_task_cost(
        self,
        provider: str,
        model: str,
        task_type: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None
    ) -> float:
        """
        Estimate cost for a single task.

        Args:
            provider: AI provider name
            model: Model name
            task_type: Type of task (parsing, reasoning, coding, etc.)
            input_tokens: Actual input tokens (or None to use estimate)
            output_tokens: Actual output tokens (or None to use estimate)

        Returns:
            Estimated cost in USD
        """
        # Ollama is always free
        if provider == "ollama":
            return 0.0

        # Get cost rates
        if provider not in PROVIDER_COSTS:
            return 0.0

        model_costs = PROVIDER_COSTS[provider].get(model)
        if not model_costs:
            # Use first available model as default
            model_costs = list(PROVIDER_COSTS[provider].values())[0]

        input_cost_per_1m, output_cost_per_1m = model_costs

        # Get token estimates
        if input_tokens is None or output_tokens is None:
            estimates = TASK_TOKEN_ESTIMATES.get(task_type, TASK_TOKEN_ESTIMATES["coding"])
            input_tokens = input_tokens or estimates["input"]
            output_tokens = output_tokens or estimates["output"]

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_1m

        return input_cost + output_cost

    def estimate_mvp_generation_cost(self, config: Dict[str, str]) -> Dict[str, float]:
        """
        Estimate cost for a full MVP generation.

        Args:
            config: Provider configuration (provider per task type)

        Returns:
            Dict with cost breakdown and total
        """
        costs = {}

        # Architect phase
        reasoning_provider = config.get("reasoning", "google")
        reasoning_model = config.get("reasoning_model", "gemini-2.5-flash-lite")
        costs["architect_tdd"] = self.estimate_task_cost(
            reasoning_provider, reasoning_model, "reasoning"
        )

        # Dev Team - TDD Parsing (4 parallel calls)
        parsing_provider = config.get("parsing", "google")
        parsing_model = config.get("parsing_model", "gemini-2.0-flash-lite")
        costs["tdd_parsing"] = self.estimate_task_cost(
            parsing_provider, parsing_model, "parsing"
        ) * 4  # 4 parallel extractions

        # Dev Team - Tech Lead decomposition
        costs["tech_lead"] = self.estimate_task_cost(
            reasoning_provider, reasoning_model, "reasoning"
        ) * 0.3  # Smaller task

        # Dev Team - Code Generation (2 parallel calls: frontend + backend)
        coding_provider = config.get("coding", "google")
        coding_model = config.get("coding_model", "gemini-2.5-flash-lite")
        costs["code_generation"] = self.estimate_task_cost(
            coding_provider, coding_model, "coding"
        ) * 2  # Frontend + Backend

        # Dev Team - Integration Review
        review_provider = config.get("review", "google")
        review_model = config.get("review_model", "gemini-2.5-flash-lite")
        costs["integration_review"] = self.estimate_task_cost(
            review_provider, review_model, "review"
        )

        # Calculate total
        costs["total"] = sum(costs.values())

        return costs

    def get_monthly_projection(self, cost_per_mvp: float, mvps_per_month: int) -> Dict[str, float]:
        """
        Project monthly costs.

        Args:
            cost_per_mvp: Cost per MVP generation
            mvps_per_month: Expected number of MVPs per month

        Returns:
            Dict with monthly projection
        """
        return {
            "cost_per_mvp": cost_per_mvp,
            "mvps_per_month": mvps_per_month,
            "monthly_cost": cost_per_mvp * mvps_per_month,
            "yearly_cost": cost_per_mvp * mvps_per_month * 12
        }

    def log_usage(
        self,
        provider: str,
        model: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ):
        """
        Log actual usage for tracking.

        Args:
            provider: AI provider name
            model: Model name
            task_type: Type of task
            input_tokens: Actual input tokens
            output_tokens: Actual output tokens
            cost: Actual cost
        """
        # Load existing log
        log_data = []
        if self.usage_log_file.exists():
            try:
                with open(self.usage_log_file, 'r') as f:
                    log_data = json.load(f)
            except Exception:
                pass

        # Add new entry
        log_data.append({
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "task_type": task_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })

        # Save log
        try:
            with open(self.usage_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Error writing usage log: {e}")

    def get_usage_summary(self, days: int = 30) -> Dict[str, any]:
        """
        Get usage summary for the last N days.

        Args:
            days: Number of days to summarize

        Returns:
            Dict with usage statistics
        """
        if not self.usage_log_file.exists():
            return {"total_cost": 0.0, "total_calls": 0}

        try:
            with open(self.usage_log_file, 'r') as f:
                log_data = json.load(f)
        except Exception:
            return {"total_cost": 0.0, "total_calls": 0}

        # Filter by date
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_entries = [
            entry for entry in log_data
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
        ]

        # Calculate summary
        total_cost = sum(entry.get("cost", 0.0) for entry in recent_entries)
        total_calls = len(recent_entries)

        # Cost by provider
        provider_costs = {}
        for entry in recent_entries:
            provider = entry.get("provider", "unknown")
            provider_costs[provider] = provider_costs.get(provider, 0.0) + entry.get("cost", 0.0)

        return {
            "period_days": days,
            "total_cost": round(total_cost, 2),
            "total_calls": total_calls,
            "average_cost_per_call": round(total_cost / total_calls if total_calls > 0 else 0.0, 4),
            "cost_by_provider": {k: round(v, 2) for k, v in provider_costs.items()}
        }


# Global estimator instance
_estimator_instance: Optional[CostEstimator] = None


def get_cost_estimator() -> CostEstimator:
    """Get or create the global cost estimator instance."""
    global _estimator_instance
    if _estimator_instance is None:
        _estimator_instance = CostEstimator()
    return _estimator_instance


def estimate_generation_cost() -> Dict[str, float]:
    """
    Estimate cost for current configuration.

    Returns:
        Dict with cost breakdown
    """
    estimator = get_cost_estimator()

    # Read current configuration
    config = {
        "reasoning": os.getenv("LLM_REASONING_PROVIDER") or os.getenv("LLM_PROVIDER", "google"),
        "parsing": os.getenv("LLM_PARSING_PROVIDER") or os.getenv("LLM_PROVIDER", "google"),
        "coding": os.getenv("LLM_CODING_PROVIDER") or os.getenv("LLM_PROVIDER", "google"),
        "review": os.getenv("LLM_REVIEW_PROVIDER") or os.getenv("LLM_PROVIDER", "google"),
    }

    return estimator.estimate_mvp_generation_cost(config)


def print_cost_estimate():
    """Print cost estimate for current configuration."""
    costs = estimate_generation_cost()

    print("\n" + "=" * 60)
    print("MVP GENERATION COST ESTIMATE")
    print("=" * 60)
    print(f"Architect TDD Generation:  ${costs['architect_tdd']:.4f}")
    print(f"TDD Parsing (4 calls):     ${costs['tdd_parsing']:.4f}")
    print(f"Tech Lead Decomposition:   ${costs['tech_lead']:.4f}")
    print(f"Code Generation (2 calls): ${costs['code_generation']:.4f}")
    print(f"Integration Review:        ${costs['integration_review']:.4f}")
    print("-" * 60)
    print(f"TOTAL PER MVP:             ${costs['total']:.4f}")
    print("=" * 60)

    # Monthly projections
    estimator = get_cost_estimator()
    for count in [10, 50, 100]:
        projection = estimator.get_monthly_projection(costs['total'], count)
        print(f"{count} MVPs/month: ${projection['monthly_cost']:.2f}/month (${projection['yearly_cost']:.2f}/year)")

    print("=" * 60 + "\n")