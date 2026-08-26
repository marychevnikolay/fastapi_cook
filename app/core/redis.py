
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_cache.backends.redis import RedisBackend
import sys
from pathlib import Path
from app.init import redis_manager
from fastapi_cache import FastAPICache

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте приложения
    await redis_manager.connect()
    FastAPICache.init(RedisBackend(redis_manager.redis), prefix="fastapi-cache")
    yield
    await redis_manager.close()
    # При выключении/перезагрузке приложения

