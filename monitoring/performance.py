# monitoring/performance.py
import time
import functools
from django.core.cache import cache


def monitor_performance(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        # Store in cache for dashboard
        key = f"perf_{func.__name__}"
        history = cache.get(key, [])
        history.append(duration)
        if len(history) > 100:
            history = history[-100:]
        cache.set(key, history, 3600)

        if duration > 1.0:  # Log slow operations
            print(f"⚠️ Slow operation: {func.__name__} took {duration:.2f}s")

        return result

    return wrapper
