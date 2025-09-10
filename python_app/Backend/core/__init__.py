from core.config.db_config import setting
from core.config.jwt_aes_config import jwt_aes_settings,Path
from core.config.config_orm import get_db_session,AsyncSession,async_engine,Session
from core.config.redis_config import r
from core.config.logging_config import logging_conf
from core.security.jwt_logic import Token_servise
from core.config.aiosmtplib_config import send_email
from core.app_logic.ban_unban import Unban,new_ban
from core.app_logic.crud_and_after import (Validation,after_registration,after_login,
                                           after_change_pass,validate_current_password,full_delete_user,
                                           create_user)
from core.app_logic.rights_check import check_token,Role_checker,safe_decode_token,validation_payload,load_user_to_redis
from core.app_logic.user_separation import return_table,create_payload_user,add_to_table,send_table
from core.app_logic.info import User_Info,Name_Full_Info,get_name,get_ban_staus
from core.app_logic.DB_command import DB_CRUD,DBError
from core.app_logic.Redis_command import RedisCRUD,RedisError
from core.app_logic.chat import check_root_for_room,websocket_chat_handler,return_chat
from core.security.utils import set_cookie,hash_pass,check_pass,encrypt,decrypt
from core.app_logic.common import html_for_email,get_grades,check_root_for_grades,router as email_router