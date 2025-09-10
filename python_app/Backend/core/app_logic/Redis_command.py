from core import r,logging_conf
import logging

logger = logging.getLogger(__name__)
logging_conf()

class RedisError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def safe_redis_call(func, *args, not_found_msg=None, **kwargs):
    try:
        result = await func(*args, **kwargs)
        if result is None and not_found_msg:
            logger.warning(not_found_msg)
            raise RedisError(not_found_msg, status_code=404)
        return result
    except Exception as e:
        logger.exception("Redis operation failed: %s", str(e))
        raise RedisError(f"Redis operation failed: {str(e)}")
logger.info("Redis operation succeeded")

class RedisCRUD:
    def __init__(self, key: str):
        if not key:
            logger.error("Attempted to initialize RedisCRUD with empty key")
            raise ValueError("Redis key must not be empty")
        self.key = key

    async def redis_set(self, value: str):
        if value is None:
            logger.error("Attempted to set Redis key with None value")
            raise ValueError("Redis value must not be None")
        await safe_redis_call(r.set, self.key, value)

    async def redis_setex(self, ttl: int ,value: str):
        if value is None or ttl <= 0:
            logger.error("Attempted to setex Redis key with invalid value or TTL: value=%s, ttl=%d", value, ttl)
            raise ValueError("Invalid value or TTL")
        await safe_redis_call(r.setex, self.key, ttl, value)

    async def redis_hset(self, mapping: dict, ttl: int | None = None):
        if not isinstance(mapping, dict) or not mapping:
            logger.error("Attempted to hset Redis key with invalid mapping: %s", mapping)
            raise ValueError("Mapping must be a non-empty dict")
        await safe_redis_call(r.hset, self.key, mapping=mapping)
        if ttl:
            await safe_redis_call(r.expire, self.key, ttl)

    async def redis_get_string(self):
        result = await safe_redis_call(r.get, self.key, not_found_msg="Key not found")
        
        return result.decode()

    async def redis_get_hash(self, field: str):
        if not field:
            logger.error("Attempted to get hash field with empty field name")
            raise ValueError("Field must not be empty")
        
        return await safe_redis_call(r.hget, self.key, field, not_found_msg="Field not found in hash")

    async def redis_get_hashall(self):
        result = await safe_redis_call(r.hgetall, self.key, not_found_msg="Hash not found")

        return {k.decode(): v.decode() for k, v in result.items()}

    async def redis_delete(self):
        deleted = await safe_redis_call(r.delete, self.key)
        if deleted == 0:
            logger.warning("Attempted to delete non-existent key: %s", self.key)
            raise RedisError("Key not found", status_code=404)
        