"""
Async LLM Executor for Parallel Processing

This module provides utilities for executing multiple LLM calls in parallel
to improve performance and reduce latency in the MVP generation pipeline.

Features:
- Async/await support for concurrent LLM calls
- Thread pool executor for CPU-bound tasks
- Rate limiting and error handling
- Progress tracking and logging
"""

import asyncio
from typing import Any, Callable, Coroutine, List, Optional, TypeVar, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import time

T = TypeVar('T')


class AsyncLLMExecutor:
    """Executor for running multiple LLM calls in parallel."""

    def __init__(self, max_workers: Optional[int] = None, timeout: Optional[float] = None):
        """
        Initialize the async executor.

        Args:
            max_workers: Maximum number of parallel workers (default: 5)
            timeout: Timeout in seconds for each task (default: 120)
        """
        self.max_workers = max_workers or 5
        self.timeout = timeout or 120.0
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    def run_parallel(
        self,
        tasks: List[Callable[[], Any]],
        task_names: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> List[Any]:
        """
        Run multiple synchronous LLM calls in parallel using thread pool.

        Args:
            tasks: List of callable tasks (functions that take no arguments)
            task_names: Optional names for each task (for logging)
            show_progress: Whether to print progress updates

        Returns:
            List of results in the same order as tasks

        Example:
            >>> executor = AsyncLLMExecutor()
            >>> tasks = [
            ...     lambda: llm1.invoke(messages1),
            ...     lambda: llm2.invoke(messages2),
            ...     lambda: llm3.invoke(messages3)
            ... ]
            >>> results = executor.run_parallel(tasks)
        """
        if not tasks:
            return []

        task_names = task_names or [f"Task {i+1}" for i in range(len(tasks))]

        if show_progress:
            print(f"\nRunning {len(tasks)} LLM calls in parallel...")
            start_time = time.time()

        # Submit all tasks
        future_to_index = {}
        for i, task in enumerate(tasks):
            future = self.executor.submit(task)
            future_to_index[future] = i

        # Collect results in order
        results = [None] * len(tasks)
        completed = 0

        for future in as_completed(future_to_index.keys(), timeout=self.timeout):
            index = future_to_index[future]
            task_name = task_names[index]

            try:
                result = future.result()
                results[index] = result
                completed += 1

                if show_progress:
                    print(f"✓ [{completed}/{len(tasks)}] {task_name} completed")

            except Exception as e:
                print(f"✗ {task_name} failed: {e}")
                results[index] = None

        if show_progress:
            elapsed = time.time() - start_time
            print(f"Parallel execution completed in {elapsed:.2f}s\n")

        return results

    async def run_async(
        self,
        coroutines: List[Coroutine[Any, Any, T]],
        task_names: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> List[T]:
        """
        Run multiple async coroutines concurrently.

        Args:
            coroutines: List of coroutines to execute
            task_names: Optional names for each task (for logging)
            show_progress: Whether to print progress updates

        Returns:
            List of results in the same order as coroutines

        Example:
            >>> executor = AsyncLLMExecutor()
            >>> coroutines = [
            ...     llm1.ainvoke(messages1),
            ...     llm2.ainvoke(messages2),
            ...     llm3.ainvoke(messages3)
            ... ]
            >>> results = await executor.run_async(coroutines)
        """
        if not coroutines:
            return []

        task_names = task_names or [f"Task {i+1}" for i in range(len(coroutines))]

        if show_progress:
            print(f"\nRunning {len(coroutines)} async LLM calls...")
            start_time = time.time()

        # Run all coroutines concurrently
        try:
            results = await asyncio.gather(*coroutines, return_exceptions=True)

            # Check for exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"{task_names[i]} failed: {result}")
                    results[i] = None
                elif show_progress:
                    print(f"✓ {task_names[i]} completed")

            if show_progress:
                elapsed = time.time() - start_time
                print(f"Async execution completed in {elapsed:.2f}s\n")

            return results

        except asyncio.TimeoutError:
            print(f"✗ Timeout after {self.timeout}s")
            raise

    def run_batch(
        self,
        task_fn: Callable[[Any], Any],
        items: List[Any],
        item_names: Optional[List[str]] = None,
        show_progress: bool = True
    ) -> List[Any]:
        """
        Run the same function on multiple items in parallel.

        Args:
            task_fn: Function to apply to each item
            items: List of items to process
            item_names: Optional names for each item (for logging)
            show_progress: Whether to print progress updates

        Returns:
            List of results in the same order as items

        Example:
            >>> executor = AsyncLLMExecutor()
            >>> def extract_features(tdd_section):
            ...     return llm.invoke(f"Extract features from: {tdd_section}")
            >>> sections = [section1, section2, section3]
            >>> results = executor.run_batch(extract_features, sections)
        """
        tasks = [partial(task_fn, item) for item in items]
        return self.run_parallel(tasks, task_names=item_names, show_progress=show_progress)

    def cleanup(self):
        """Cleanup the executor resources."""
        self.executor.shutdown(wait=True)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


# Convenience functions for common patterns

def parallel_invoke(
    llm_tasks: List[tuple[Any, List[Any]]],
    task_names: Optional[List[str]] = None,
    show_progress: bool = True
) -> List[Any]:
    """
    Invoke multiple LLMs with their respective messages in parallel.

    Args:
        llm_tasks: List of (llm, messages) tuples
        task_names: Optional names for each task
        show_progress: Whether to print progress

    Returns:
        List of LLM responses

    Example:
        >>> results = parallel_invoke([
        ...     (llm1, messages1),
        ...     (llm2, messages2),
        ...     (llm3, messages3)
        ... ])
    """
    with AsyncLLMExecutor() as executor:
        tasks = [lambda llm=llm, msg=msg: llm.invoke(msg) for llm, msg in llm_tasks]
        return executor.run_parallel(tasks, task_names=task_names, show_progress=show_progress)


async def async_parallel_invoke(
    llm_tasks: List[tuple[Any, List[Any]]],
    task_names: Optional[List[str]] = None,
    show_progress: bool = True
) -> List[Any]:
    """
    Async version: Invoke multiple LLMs with their respective messages concurrently.

    Args:
        llm_tasks: List of (llm, messages) tuples
        task_names: Optional names for each task
        show_progress: Whether to print progress

    Returns:
        List of LLM responses

    Example:
        >>> results = await async_parallel_invoke([
        ...     (llm1, messages1),
        ...     (llm2, messages2),
        ...     (llm3, messages3)
        ... ])
    """
    executor = AsyncLLMExecutor()
    coroutines = [llm.ainvoke(msg) for llm, msg in llm_tasks]
    return await executor.run_async(coroutines, task_names=task_names, show_progress=show_progress)


def parallel_structured_output(
    llm_schema_tasks: List[tuple[Any, Any, List[Any]]],
    task_names: Optional[List[str]] = None,
    show_progress: bool = True
) -> List[Any]:
    """
    Invoke multiple LLMs with structured output in parallel.

    Args:
        llm_schema_tasks: List of (llm, schema, messages) tuples
        task_names: Optional names for each task
        show_progress: Whether to print progress

    Returns:
        List of structured outputs

    Example:
        >>> results = parallel_structured_output([
        ...     (llm1, TechStackSchema, messages1),
        ...     (llm2, FeaturesSchema, messages2),
        ...     (llm3, APIsSchema, messages3)
        ... ])
    """
    with AsyncLLMExecutor() as executor:
        tasks = [
            lambda llm=llm, schema=schema, msg=msg: llm.with_structured_output(schema).invoke(msg)
            for llm, schema, msg in llm_schema_tasks
        ]
        return executor.run_parallel(tasks, task_names=task_names, show_progress=show_progress)


def benchmark_providers(
    providers: List[str],
    test_messages: List[Any],
    task_type: str = "coding"
) -> Dict[str, float]:
    """
    Benchmark multiple providers on the same task.

    Args:
        providers: List of provider names to test
        test_messages: Messages to send to each provider
        task_type: Type of task for model selection

    Returns:
        Dict mapping provider name to response time in seconds

    Example:
        >>> from langchain_core.messages import HumanMessage
        >>> messages = [HumanMessage(content="Write a hello world function")]
        >>> times = benchmark_providers(["google", "anthropic", "openai"], messages)
        >>> print(times)  # {'google': 1.23, 'anthropic': 2.45, 'openai': 1.87}
    """
    from .llm_factory import get_llm

    results = {}

    print(f"\nBenchmarking {len(providers)} providers...")

    for provider in providers:
        try:
            llm = get_llm(task_type=task_type, provider=provider)

            start_time = time.time()
            response = llm.invoke(test_messages)
            elapsed = time.time() - start_time

            results[provider] = elapsed
            print(f"  {provider}: {elapsed:.2f}s")

        except Exception as e:
            print(f"  {provider}: Failed ({e})")
            results[provider] = float('inf')

    print()
    return results