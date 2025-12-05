"""
LLM Factory for Multi-Provider Support

This module provides a unified interface for creating LLM instances
from multiple providers (Google, Anthropic, OpenAI, Ollama).

Features:
- Automatic provider selection based on environment variables
- Task-specific model optimization (fast vs powerful)
- Fallback chain for reliability
- Cost optimization options
"""

import os
from typing import Optional, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel

# Optional imports for other providers
try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


# Task categories for model selection
TaskType = Literal[
    "parsing",      # Fast: Job description parsing, data extraction
    "reasoning",    # Powerful: TDD generation, complex analysis
    "coding",       # Balanced: Code generation
    "review",       # Balanced: Integration review, validation
    "creative"      # Creative: Query generation, ideation
]


# Model configurations by provider and task type
MODEL_CONFIGS = {
    "google": {
        "parsing": {"model": "gemini-2.0-flash-lite", "temperature": 0.2},
        "reasoning": {"model": "gemini-2.0-flash-thinking-exp", "temperature": 0.4},
        "coding": {"model": "gemini-2.5-flash-lite", "temperature": 0.3},
        "review": {"model": "gemini-2.5-flash-lite", "temperature": 0.2},
        "creative": {"model": "gemini-2.5-flash-lite", "temperature": 0.7},
    },
    "anthropic": {
        "parsing": {"model": "claude-3-5-haiku-20241022", "temperature": 0.2},
        "reasoning": {"model": "claude-3-7-sonnet-20250219", "temperature": 0.4},
        "coding": {"model": "claude-3-7-sonnet-20250219", "temperature": 0.3},
        "review": {"model": "claude-3-5-sonnet-20241022", "temperature": 0.2},
        "creative": {"model": "claude-3-5-sonnet-20241022", "temperature": 0.7},
    },
    "openai": {
        "parsing": {"model": "gpt-4o-mini", "temperature": 0.2},
        "reasoning": {"model": "o1", "temperature": 1.0},
        "coding": {"model": "gpt-4o", "temperature": 0.3},
        "review": {"model": "gpt-4o", "temperature": 0.2},
        "creative": {"model": "gpt-4o", "temperature": 0.7},
    },
    "ollama": {
        "parsing": {"model": "qwen2.5-coder:3b", "temperature": 0.2},
        "reasoning": {"model": "llama3.2:latest", "temperature": 0.4},
        "coding": {"model": "qwen2.5-coder:7b", "temperature": 0.3},
        "review": {"model": "qwen2.5-coder:3b", "temperature": 0.2},
        "creative": {"model": "llama3.2:latest", "temperature": 0.7},
    }
}

# Budget mode configurations - use smallest/cheapest models
BUDGET_MODEL_CONFIGS = {
    "google": {
        # Use same models but with Gemini free tier
        "parsing": {"model": "gemini-2.0-flash-lite", "temperature": 0.2},
        "reasoning": {"model": "gemini-2.0-flash-lite", "temperature": 0.4},  # Cheaper than thinking model
        "coding": {"model": "gemini-2.0-flash-lite", "temperature": 0.3},
        "review": {"model": "gemini-2.0-flash-lite", "temperature": 0.2},
        "creative": {"model": "gemini-2.0-flash-lite", "temperature": 0.7},
    },
    "ollama": {
        # Use smallest viable models
        "parsing": {"model": "qwen2.5-coder:1.5b", "temperature": 0.2},
        "reasoning": {"model": "phi3:mini", "temperature": 0.4},
        "coding": {"model": "qwen2.5-coder:3b", "temperature": 0.3},
        "review": {"model": "phi3:mini", "temperature": 0.2},
        "creative": {"model": "phi3:mini", "temperature": 0.7},
    }
}


class LLMFactory:
    """Factory class for creating LLM instances with multi-provider support."""

    def __init__(self):
        """Initialize the LLM factory with environment-based configuration."""
        # Get primary provider from environment (default: google)
        self.primary_provider = os.getenv("LLM_PROVIDER", "google").lower()

        # Get fallback providers (comma-separated)
        fallback_str = os.getenv("LLM_FALLBACK_PROVIDERS", "")
        self.fallback_providers = [p.strip().lower() for p in fallback_str.split(",") if p.strip()]

        # Budget mode - use smallest/cheapest models
        self.budget_mode = os.getenv("BUDGET_MODE", "false").lower() in ("true", "1", "yes", "ultra")
        self.ultra_budget = os.getenv("BUDGET_MODE", "").lower() == "ultra"

        # Task-specific provider overrides (e.g., use Google for reasoning, Ollama for rest)
        self.provider_overrides = {
            "parsing": os.getenv("LLM_PARSING_PROVIDER"),
            "reasoning": os.getenv("LLM_REASONING_PROVIDER"),
            "coding": os.getenv("LLM_CODING_PROVIDER"),
            "review": os.getenv("LLM_REVIEW_PROVIDER"),
            "creative": os.getenv("LLM_CREATIVE_PROVIDER"),
        }

        # Model overrides for Ollama (allow custom model selection)
        self.ollama_model_overrides = {
            "parsing": os.getenv("OLLAMA_PARSING_MODEL"),
            "reasoning": os.getenv("OLLAMA_REASONING_MODEL"),
            "coding": os.getenv("OLLAMA_CODING_MODEL"),
            "review": os.getenv("OLLAMA_REVIEW_MODEL"),
            "creative": os.getenv("OLLAMA_CREATIVE_MODEL"),
        }

        # Validate providers
        self._validate_providers()

    def _validate_providers(self):
        """Validate that required providers are available and configured."""
        providers = [self.primary_provider] + self.fallback_providers

        for provider in providers:
            if provider == "google":
                if not os.getenv("GOOGLE_API_KEY"):
                    print(f"⚠️  Warning: GOOGLE_API_KEY not set for provider '{provider}'")

            elif provider == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    print(f"⚠️  Warning: langchain-anthropic not installed for provider '{provider}'")
                if not os.getenv("ANTHROPIC_API_KEY"):
                    print(f"⚠️  Warning: ANTHROPIC_API_KEY not set for provider '{provider}'")

            elif provider == "openai":
                if not OPENAI_AVAILABLE:
                    print(f"⚠️  Warning: langchain-openai not installed for provider '{provider}'")
                if not os.getenv("OPENAI_API_KEY"):
                    print(f"⚠️  Warning: OPENAI_API_KEY not set for provider '{provider}'")

            elif provider == "ollama":
                if not OLLAMA_AVAILABLE:
                    print(f"⚠️  Warning: langchain-ollama not installed for provider '{provider}'")

    def get_llm(
        self,
        task_type: TaskType = "coding",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> BaseChatModel:
        """
        Get an LLM instance optimized for the specified task type.

        Args:
            task_type: Type of task (parsing, reasoning, coding, review, creative)
            provider: Override provider (default: use factory's primary provider)
            model: Override model name (default: use task-optimized model)
            temperature: Override temperature (default: use task-optimized temperature)
            **kwargs: Additional provider-specific arguments

        Returns:
            BaseChatModel: Configured LLM instance

        Raises:
            ValueError: If provider is not supported or not configured
        """
        # Check for task-specific provider override
        if self.provider_overrides.get(task_type):
            provider = self.provider_overrides[task_type].lower()
        else:
            # Use specified provider or fall back to primary
            provider = (provider or self.primary_provider).lower()

        # Get model configuration for this provider and task type
        if provider not in MODEL_CONFIGS:
            raise ValueError(f"Unsupported provider: {provider}")

        # Select config based on budget mode
        if self.budget_mode and provider in BUDGET_MODEL_CONFIGS:
            config = BUDGET_MODEL_CONFIGS[provider].get(task_type, BUDGET_MODEL_CONFIGS[provider]["coding"])
        else:
            config = MODEL_CONFIGS[provider].get(task_type, MODEL_CONFIGS[provider]["coding"])

        # Apply Ollama model overrides if specified
        if provider == "ollama" and self.ollama_model_overrides.get(task_type):
            config = {**config, "model": self.ollama_model_overrides[task_type]}

        # Override with explicit parameters if provided
        final_model = model or config["model"]
        final_temperature = temperature if temperature is not None else config["temperature"]

        # Create LLM instance based on provider
        try:
            if provider == "google":
                return self._create_google_llm(final_model, final_temperature, **kwargs)
            elif provider == "anthropic":
                return self._create_anthropic_llm(final_model, final_temperature, **kwargs)
            elif provider == "openai":
                return self._create_openai_llm(final_model, final_temperature, **kwargs)
            elif provider == "ollama":
                return self._create_ollama_llm(final_model, final_temperature, **kwargs)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            # Try fallback providers
            if self.fallback_providers:
                print(f"⚠️  Failed to create LLM with {provider}: {e}")
                print(f"🔄 Trying fallback providers: {self.fallback_providers}")

                for fallback_provider in self.fallback_providers:
                    try:
                        return self.get_llm(
                            task_type=task_type,
                            provider=fallback_provider,
                            temperature=final_temperature,
                            **kwargs
                        )
                    except Exception as fallback_error:
                        print(f"⚠️  Fallback {fallback_provider} also failed: {fallback_error}")
                        continue

            # No fallback worked, raise original error
            raise e

    def _create_google_llm(self, model: str, temperature: float, **kwargs) -> ChatGoogleGenerativeAI:
        """Create Google Gemini LLM instance."""
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            **kwargs
        )

    def _create_anthropic_llm(self, model: str, temperature: float, **kwargs) -> BaseChatModel:
        """Create Anthropic Claude LLM instance."""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("langchain-anthropic not installed. Install with: pip install langchain-anthropic")

        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            **kwargs
        )

    def _create_openai_llm(self, model: str, temperature: float, **kwargs) -> BaseChatModel:
        """Create OpenAI GPT LLM instance."""
        if not OPENAI_AVAILABLE:
            raise ImportError("langchain-openai not installed. Install with: pip install langchain-openai")

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable not set")

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            **kwargs
        )

    def _create_ollama_llm(self, model: str, temperature: float, **kwargs) -> BaseChatModel:
        """Create Ollama local LLM instance."""
        if not OLLAMA_AVAILABLE:
            raise ImportError("langchain-ollama not installed. Install with: pip install langchain-ollama")

        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            **kwargs
        )

    def get_parallel_llms(
        self,
        task_types: list[TaskType],
        providers: Optional[list[str]] = None,
        **kwargs
    ) -> list[BaseChatModel]:
        """
        Get multiple LLM instances for parallel execution.

        Args:
            task_types: List of task types for each LLM
            providers: Optional list of providers (one per task type)
            **kwargs: Additional arguments passed to get_llm

        Returns:
            list[BaseChatModel]: List of configured LLM instances
        """
        if providers and len(providers) != len(task_types):
            raise ValueError("providers list must match task_types length")

        llms = []
        for i, task_type in enumerate(task_types):
            provider = providers[i] if providers else None
            llm = self.get_llm(task_type=task_type, provider=provider, **kwargs)
            llms.append(llm)

        return llms


# Global factory instance
_factory_instance: Optional[LLMFactory] = None


def get_llm_factory() -> LLMFactory:
    """Get or create the global LLM factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = LLMFactory()
    return _factory_instance


def get_llm(
    task_type: TaskType = "coding",
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> BaseChatModel:
    """
    Convenience function to get an LLM instance.

    Args:
        task_type: Type of task (parsing, reasoning, coding, review, creative)
        provider: Override provider (default: use configured primary provider)
        model: Override model name (default: use task-optimized model)
        temperature: Override temperature (default: use task-optimized temperature)
        **kwargs: Additional provider-specific arguments

    Returns:
        BaseChatModel: Configured LLM instance

    Example:
        >>> # Get a fast model for parsing
        >>> llm = get_llm(task_type="parsing")

        >>> # Get a powerful model for code generation
        >>> llm = get_llm(task_type="coding", provider="anthropic")

        >>> # Override specific parameters
        >>> llm = get_llm(task_type="reasoning", model="gpt-4", temperature=0.5)
    """
    factory = get_llm_factory()
    return factory.get_llm(
        task_type=task_type,
        provider=provider,
        model=model,
        temperature=temperature,
        **kwargs
    )