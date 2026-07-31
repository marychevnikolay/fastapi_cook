from app.connectors.redis_connector import RedisManager
from app.core.config import settings

redis_manager = RedisManager(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
)
