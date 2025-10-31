from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from src.core.config.env import env


async def get_redis_pool() -> ArqRedis:
    """
    Get ARQ Redis pool for enqueueing jobs.

    Returns:
        ArqRedis pool instance
    """
    return await create_pool(
        RedisSettings(
            host=env.REDIS_HOST,
            port=env.REDIS_PORT,
            database=env.REDIS_DB,
        )
    )
