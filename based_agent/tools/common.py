"""Helpers shared by agent tools."""

import functools
from collections.abc import Callable


def tool(action: str) -> Callable:
    """Turn exceptions raised by a tool into an error string for the LLM.

    Swarm reads the function name, docstring, and signature to build the tool
    schema; ``functools.wraps`` preserves all three.

    Args:
        action: Short description used in the error, e.g. "deploying NFT".
    """

    def decorator(func: Callable[..., str]) -> Callable[..., str]:

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> str:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return f"Error {action}: {e}"

        return wrapper

    return decorator
