"""
Enhanced async LLM processing with batching and parallelization.
Improves performance for multiple LLM calls.
"""

import asyncio
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

from src.utils.logger import setup_logger
from src.core.response_cache import ResponseCache

logger = setup_logger(__name__)


@dataclass
class LLMRequest:
    """Represents a single LLM request."""
    id: str
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMResponse:
    """Represents an LLM response."""
    request_id: str
    content: str
    tokens_used: int
    duration: float
    cached: bool = False
    error: Optional[str] = None


class AsyncLLMProcessor:
    """
    Process multiple LLM requests asynchronously with batching and caching.
    
    Features:
    - Parallel request processing
    - Request batching
    - Response caching
    - Rate limiting
    - Error handling and retries
    """
    
    def __init__(
        self,
        llm_callable: Callable,
        cache: Optional[ResponseCache] = None,
        max_concurrent: int = 5,
        batch_size: int = 10,
        retry_attempts: int = 3,
    ):
        """
        Initialize async processor.
        
        Args:
            llm_callable: Function to call for LLM requests
            cache: Optional response cache
            max_concurrent: Maximum concurrent requests
            batch_size: Maximum batch size
            retry_attempts: Number of retry attempts on failure
        """
        self.llm_callable = llm_callable
        self.cache = cache
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        logger.info(
            f"AsyncLLMProcessor initialized: "
            f"max_concurrent={max_concurrent}, batch_size={batch_size}"
        )
    
    async def process_single(
        self,
        request: LLMRequest,
        retry_count: int = 0
    ) -> LLMResponse:
        """
        Process a single LLM request asynchronously.
        
        Args:
            request: LLM request to process
            retry_count: Current retry attempt number
            
        Returns:
            LLM response
        """
        async with self.semaphore:
            start_time = datetime.now()
            
            # Check cache
            if self.cache:
                cache_key = self.cache.get_cache_key(
                    request.prompt,
                    request.model
                )
                cached_response = self.cache.get(cache_key)
                
                if cached_response:
                    logger.debug(f"Cache hit for request {request.id}")
                    duration = (datetime.now() - start_time).total_seconds()
                    return LLMResponse(
                        request_id=request.id,
                        content=cached_response.get('content', ''),
                        tokens_used=cached_response.get('tokens_used', 0),
                        duration=duration,
                        cached=True
                    )
            
            try:
                # Make async LLM call
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.llm_callable(
                        prompt=request.prompt,
                        model=request.model,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    )
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                # Extract content and token usage
                content = self._extract_content(response)
                tokens_used = self._extract_tokens(response)
                
                # Cache response
                if self.cache:
                    self.cache.set(cache_key, {
                        'content': content,
                        'tokens_used': tokens_used,
                        'timestamp': datetime.now().timestamp()
                    })
                
                logger.info(
                    f"Request {request.id} completed in {duration:.2f}s "
                    f"({tokens_used} tokens)"
                )
                
                return LLMResponse(
                    request_id=request.id,
                    content=content,
                    tokens_used=tokens_used,
                    duration=duration,
                    cached=False
                )
                
            except Exception as e:
                logger.error(f"Error processing request {request.id}: {e}")
                
                # Retry logic
                if retry_count < self.retry_attempts:
                    logger.info(
                        f"Retrying request {request.id} "
                        f"(attempt {retry_count + 1}/{self.retry_attempts})"
                    )
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    return await self.process_single(request, retry_count + 1)
                
                # Max retries exceeded
                duration = (datetime.now() - start_time).total_seconds()
                return LLMResponse(
                    request_id=request.id,
                    content="",
                    tokens_used=0,
                    duration=duration,
                    cached=False,
                    error=str(e)
                )
    
    async def process_batch(
        self,
        requests: List[LLMRequest]
    ) -> List[LLMResponse]:
        """
        Process a batch of LLM requests concurrently.
        
        Args:
            requests: List of LLM requests
            
        Returns:
            List of LLM responses in the same order
        """
        if not requests:
            return []
        
        logger.info(f"Processing batch of {len(requests)} requests")
        
        # Create tasks for all requests
        tasks = [self.process_single(req) for req in requests]
        
        # Execute all tasks concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        results = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Request {requests[i].id} failed: {response}")
                results.append(LLMResponse(
                    request_id=requests[i].id,
                    content="",
                    tokens_used=0,
                    duration=0.0,
                    cached=False,
                    error=str(response)
                ))
            else:
                results.append(response)
        
        return results
    
    async def process_all(
        self,
        requests: List[LLMRequest]
    ) -> List[LLMResponse]:
        """
        Process all requests in batches.
        
        Args:
            requests: List of all LLM requests
            
        Returns:
            List of all responses
        """
        if not requests:
            return []
        
        logger.info(
            f"Processing {len(requests)} total requests "
            f"in batches of {self.batch_size}"
        )
        
        all_responses = []
        
        # Process in batches
        for i in range(0, len(requests), self.batch_size):
            batch = requests[i:i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}")
            
            batch_responses = await self.process_batch(batch)
            all_responses.extend(batch_responses)
        
        # Calculate statistics
        successful = sum(1 for r in all_responses if not r.error)
        cached = sum(1 for r in all_responses if r.cached)
        total_tokens = sum(r.tokens_used for r in all_responses)
        total_duration = sum(r.duration for r in all_responses)
        
        logger.info(
            f"Completed all requests: "
            f"{successful}/{len(requests)} successful, "
            f"{cached} cached, "
            f"{total_tokens} tokens, "
            f"{total_duration:.2f}s total"
        )
        
        return all_responses
    
    def _extract_content(self, response: Any) -> str:
        """Extract content from LLM response."""
        if isinstance(response, str):
            return response
        if hasattr(response, 'content'):
            return response.content
        if isinstance(response, dict):
            return response.get('content', response.get('text', ''))
        return str(response)
    
    def _extract_tokens(self, response: Any) -> int:
        """Extract token count from LLM response."""
        if isinstance(response, dict):
            usage = response.get('usage', {})
            return usage.get('total_tokens', 0)
        if hasattr(response, 'usage'):
            return getattr(response.usage, 'total_tokens', 0)
        return 0


# Convenience functions

async def process_prompts_async(
    prompts: List[str],
    llm_callable: Callable,
    model: str = "gemini-pro",
    cache: Optional[ResponseCache] = None,
    **kwargs
) -> List[LLMResponse]:
    """
    Process multiple prompts asynchronously.
    
    Args:
        prompts: List of prompt strings
        llm_callable: LLM function to call
        model: Model name
        cache: Optional response cache
        **kwargs: Additional processor options
        
    Returns:
        List of responses
    """
    requests = [
        LLMRequest(
            id=f"req_{i}",
            prompt=prompt,
            model=model
        )
        for i, prompt in enumerate(prompts)
    ]
    
    processor = AsyncLLMProcessor(llm_callable, cache=cache, **kwargs)
    return await processor.process_all(requests)


def run_async_processing(
    prompts: List[str],
    llm_callable: Callable,
    **kwargs
) -> List[LLMResponse]:
    """
    Synchronous wrapper for async processing.
    
    Args:
        prompts: List of prompts
        llm_callable: LLM function
        **kwargs: Additional options
        
    Returns:
        List of responses
    """
    return asyncio.run(process_prompts_async(prompts, llm_callable, **kwargs))
