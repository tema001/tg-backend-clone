from inspect import signature
from typing import Dict, Callable


def resolve_kwargs(func: Callable) -> Dict:
    # kwargs = {}
    # for name, parameter in signature(func).parameters.items():
    #     if value := di_cache.get(parameter.annotation):
    #         kwargs[name] = value

    kwargs = {name: di_cache[parameter.annotation]
              for name, parameter in signature(func).parameters.items()
              if parameter.annotation in di_cache}

    return kwargs


def inject(func: Callable):
    async def wrapper(self):
        kwargs = resolve_kwargs(func)
        return await func(self, **kwargs)

    return wrapper


di_cache = {}
