from aiosmtplib import SMTP
from pydantic_settings import BaseSettings
from core import logging_conf
from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)
logging_conf()

class SMTP_Setting(BaseSettings):
   SMTP_EMAIL : str
   SMTP_PASS : str
   SMTP_HOST : str
   SMTP_PORT : int
   SMTP_TLS : bool = True

   class Config:
      env_file = ".env"
      extra = "ignore"
try:
  smtp_setting = SMTP_Setting()
  logger.info("SMTP configuration loaded successfully")

except Exception as e:
   logger.critical("Failed to load SMTP configuration: %s", str(e))
   print("Failed to load SMTP configuration:", e)

async def send_email(recipient : str,subject : str,content : str):
    message = EmailMessage()
    message["From"] = "Medical"
    message["To"] = recipient
    message["Subject"] = subject

    message.add_alternative(content, subtype="html")

    stmp = SMTP(hostname=smtp_setting.SMTP_HOST,port=smtp_setting.SMTP_PORT,start_tls=smtp_setting.SMTP_TLS)
    await stmp.connect()
    await stmp.login(smtp_setting.SMTP_EMAIL,smtp_setting.SMTP_PASS)
    await stmp.send_message(message)
    await stmp.quit()

