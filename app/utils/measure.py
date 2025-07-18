import asyncio
import time
from functools import wraps


def measure_exe_time(func):
    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(
                f"Function {func.__name__} took {elapsed_time:.4f} seconds to complete."
            )
            return result

        return async_wrapper
    else:

        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(
                f"Function {func.__name__} took {elapsed_time:.4f} seconds to complete."
            )
            return result

    return wrapper
