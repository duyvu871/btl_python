from redis.asyncio import from_url

from src.core.config.env import env


async def get_redis():
    redis = await from_url(env.REDIS_URL, decode_responses=False)
    try:
        yield redis
    finally:
        await redis.close()


async def get_redis_instance():
    redis = await from_url(env.REDIS_URL, decode_responses=True)
    return redis