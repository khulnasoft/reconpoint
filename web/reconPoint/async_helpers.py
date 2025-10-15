"""
Async utilities and helpers for reconPoint.
"""
import asyncio
import logging
from typing import List, Callable, Any, Optional, Coroutine
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

logger = logging.getLogger(__name__)


class AsyncTaskManager:
    """Manage async task execution with concurrency control."""
    
    def __init__(self, max_workers: int = 10):
        """
        Initialize async task manager.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def run_parallel(
        self,
        func: Callable,
        items: List[Any],
        timeout: Optional[int] = None
    ) -> List[Any]:
        """
        Run function in parallel for multiple items.
        
        Args:
            func: Function to execute
            items: List of items to process
            timeout: Timeout in seconds for each task
            
        Returns:
            List of results
        """
        results = []
        futures = []
        
        # Submit all tasks
        for item in items:
            future = self.executor.submit(func, item)
            futures.append((future, item))
        
        # Collect results
        for future, item in futures:
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing item {item}: {e}")
                results.append(None)
        
        return results
    
    def run_with_callback(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ):
        """
        Run function in parallel with callbacks.
        
        Args:
            func: Function to execute
            items: List of items to process
            callback: Success callback function
            error_callback: Error callback function
        """
        futures = {
            self.executor.submit(func, item): item
            for item in items
        }
        
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                if callback:
                    callback(item, result)
            except Exception as e:
                logger.error(f"Error processing item {item}: {e}")
                if error_callback:
                    error_callback(item, e)
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown executor.
        
        Args:
            wait: Whether to wait for pending tasks
        """
        self.executor.shutdown(wait=wait)


class BatchProcessor:
    """Process items in batches with concurrency control."""
    
    def __init__(self, batch_size: int = 100, max_workers: int = 5):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items per batch
            max_workers: Maximum concurrent batches
        """
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_batches(
        self,
        items: List[Any],
        process_func: Callable[[List[Any]], Any]
    ) -> List[Any]:
        """
        Process items in batches.
        
        Args:
            items: List of items to process
            process_func: Function to process each batch
            
        Returns:
            List of batch results
        """
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(process_func, batch)
                for batch in batches
            ]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    results.append(None)
        
        return results


def async_to_sync(async_func: Coroutine) -> Any:
    """
    Convert async function to sync.
    
    Args:
        async_func: Async function to convert
        
    Returns:
        Result of async function
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_func)
    finally:
        loop.close()


def run_async_in_thread(async_func: Coroutine) -> Any:
    """
    Run async function in a separate thread.
    
    Args:
        async_func: Async function to run
        
    Returns:
        Result of async function
    """
    import threading
    
    result = [None]
    exception = [None]
    
    def run():
        try:
            result[0] = async_to_sync(async_func)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    
    if exception[0]:
        raise exception[0]
    
    return result[0]


def throttle(calls_per_second: int):
    """
    Decorator to throttle function calls.
    
    Args:
        calls_per_second: Maximum calls per second
        
    Returns:
        Decorated function
    """
    import time
    
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            
            last_called[0] = time.time()
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def debounce(wait_seconds: float):
    """
    Decorator to debounce function calls.
    
    Args:
        wait_seconds: Seconds to wait before executing
        
    Returns:
        Decorated function
    """
    import time
    import threading
    
    def decorator(func):
        timer = [None]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            def call_func():
                func(*args, **kwargs)
            
            if timer[0]:
                timer[0].cancel()
            
            timer[0] = threading.Timer(wait_seconds, call_func)
            timer[0].start()
        
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self, rate: int, per: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            rate: Number of tokens
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = None
    
    def allow(self) -> bool:
        """
        Check if action is allowed.
        
        Returns:
            True if allowed, False otherwise
        """
        import time
        
        current = time.time()
        
        if self.last_check is None:
            self.last_check = current
            return True
        
        time_passed = current - self.last_check
        self.last_check = current
        
        self.allowance += time_passed * (self.rate / self.per)
        
        if self.allowance > self.rate:
            self.allowance = self.rate
        
        if self.allowance < 1.0:
            return False
        
        self.allowance -= 1.0
        return True
    
    def wait(self):
        """Wait until action is allowed."""
        import time
        
        while not self.allow():
            time.sleep(0.1)


def timeout(seconds: int):
    """
    Decorator to add timeout to function.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function
    """
    import signal
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds}s")
            
            # Set timeout handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                # Restore old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
            return result
        
        return wrapper
    return decorator


class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self, total: int, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total: Total number of items
            description: Description of operation
        """
        self.total = total
        self.current = 0
        self.description = description
        self.start_time = None
    
    def start(self):
        """Start tracking progress."""
        import time
        self.start_time = time.time()
        self.log_progress()
    
    def update(self, increment: int = 1):
        """
        Update progress.
        
        Args:
            increment: Number of items completed
        """
        self.current += increment
        
        # Log every 10%
        if self.current % max(1, self.total // 10) == 0:
            self.log_progress()
    
    def log_progress(self):
        """Log current progress."""
        import time
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            rate = self.current / elapsed if elapsed > 0 else 0
            remaining = (self.total - self.current) / rate if rate > 0 else 0
            
            logger.info(
                f"{self.description}: {self.current}/{self.total} "
                f"({self.current * 100 // self.total}%) - "
                f"{rate:.1f} items/s - "
                f"ETA: {remaining:.0f}s"
            )
        else:
            logger.info(f"{self.description}: {self.current}/{self.total}")
    
    def finish(self):
        """Mark progress as finished."""
        import time
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            logger.info(
                f"{self.description}: Completed {self.total} items in {elapsed:.1f}s"
            )
