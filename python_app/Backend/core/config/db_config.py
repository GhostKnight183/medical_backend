from pydantic_settings import BaseSettings
from core.config.logging_config import logging_conf
import logging

logger = logging.getLogger(__name__)
logging_conf()

class DB_Setting(BaseSettings):
    DB_HOST: str 
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    class Config:
      env_file = ".env"
      extra = "ignore"

    @property
    def DB_asyncpg(self):
       return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

try:
  setting = DB_Setting()
  logger.info("Database configuration loaded successfully")

except Exception as e:
   logging.critical("Failed to load database configuration: %s", str(e))
   print("Failed to load database configuration:", e)