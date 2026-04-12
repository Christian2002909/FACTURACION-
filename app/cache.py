"""
Cache y optimización de tokens para el sistema de facturación.
Reduce llamadas repetidas y optimiza consumo de API.
"""
from functools import lru_cache, wraps
from typing import Any, Callable
from datetime import datetime, timedelta
import json

# Cache en memoria con expiración
class CacheWithExpiry:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl = ttl_seconds
        self.store = {}
        self.timestamps = {}

    def get(self, key: str) -> Any:
        if key in self.store:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                return self.store[key]
            else:
                del self.store[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self.store[key] = value
        self.timestamps[key] = datetime.now()

    def clear(self) -> None:
        self.store.clear()
        self.timestamps.clear()


# Cache global
_cache = CacheWithExpiry(ttl_seconds=3600)


def cache_response(ttl: int = 3600):
    """Decorador para cachear respuestas de funciones."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{json.dumps(str(args) + str(kwargs))}"
            cached = _cache.get(cache_key)
            if cached is not None:
                return cached
            result = await func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{json.dumps(str(args) + str(kwargs))}"
            cached = _cache.get(cache_key)
            if cached is not None:
                return cached
            result = func(*args, **kwargs)
            _cache.set(cache_key, result)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


# Prompt caching para Claude API
class PromptCacheManager:
    """
    Gestiona caching de prompts para la API de Claude.
    Reduce tokens y costos en llamadas repetidas.
    """

    def __init__(self):
        self.cache = {}

    def get_cached_response(self, prompt_hash: str) -> dict | None:
        """Obtiene respuesta cacheada si existe."""
        return self.cache.get(prompt_hash)

    def cache_response(self, prompt_hash: str, response: dict, ttl: int = 86400):
        """Cachea respuesta de Claude con expiración."""
        self.cache[prompt_hash] = {
            "response": response,
            "timestamp": datetime.now(),
            "ttl": ttl
        }

    def is_expired(self, prompt_hash: str) -> bool:
        """Verifica si el cache expiró."""
        if prompt_hash not in self.cache:
            return True
        cached = self.cache[prompt_hash]
        age = (datetime.now() - cached["timestamp"]).total_seconds()
        return age > cached["ttl"]


import asyncio

# Instancia global
prompt_cache = PromptCacheManager()


# Optimizaciones de queries a BD
class QueryOptimizations:
    """Optimizaciones para reducir queries repetidas."""

    @staticmethod
    def get_select_columns(model, fields: list[str] = None):
        """
        Selecciona solo las columnas necesarias en lugar de todas.
        Reduce data transferida.
        """
        if fields:
            return [getattr(model, f) for f in fields if hasattr(model, f)]
        return model


# Uso en routers:
# @cache_response(ttl=3600)
# async def get_clientes():
#     return await db.query(Cliente).all()
