import functools


def raise_if_none(error):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if result is None:
                raise error()
            return result

        return wrapper

    return decorator
