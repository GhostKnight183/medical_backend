import asyncio
import redis.asyncio as redis
from core.config.logging_config import logging_conf
import logging

logger = logging.getLogger(__name__)
logging_conf()

try:
  r = redis.Redis(host="redis",port=6379)
  logger.info("Redis connection established successfully")

except Exception as e:
    logger.critical("Failed to connect to Redis: %s", str(e))
    print("Failed to connect to Redis:", e)