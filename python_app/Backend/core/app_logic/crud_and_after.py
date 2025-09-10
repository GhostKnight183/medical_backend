from sсhemas import User_login,User_registration,Update_password
from models import UsersAuth,Token_Storage,Token_type
from fastapi import HTTPException
from sqlalchemy import select
from core import Session,Token_servise,r,logging_conf,jwt_aes_settings as jwt_settings
from core.app_logic.user_separation import create_payload_user,add_to_table,return_table
from core.app_logic.DB_command import DB_CRUD
from core.app_logic.Redis_command import RedisCRUD
from core.security.utils import check_pass,encrypt,hash_pass
from datetime import datetime,timedelta
import logging

logger = logging.getLogger(__name__)
logging_conf()

class Validation():
    def __init__(self,session : Session):
        self.session = session
    
    async def select_to_db(self,user):
        query = (select(UsersAuth).filter(UsersAuth.email == user))

        result = await self.session.execute(query)

        logger.info("Database query executed for user: %s", user)
        return result.scalars().first()

    async def login(self,stored_user : User_login):
        user = await self.select_to_db(stored_user.email)
        if not user or not check_pass(user.password,stored_user.password) :
            logger.warning("Login attempt with non-existent user: %s", stored_user.email)
            raise HTTPException(status_code=404,detail="Incorrect email or password")
        user_dict = {
            "user_id" : user.id,
            "email" : user.email,
            "role" : user.role,
            "is_banned" : user.is_banned
        }
        logger.info("User %s successfully logged in", stored_user.email)
        return user_dict
    
    async def registration(self,stored_user : User_registration):
        user = await self.select_to_db(stored_user.email)
        if user:
            logger.warning("Attempt to register an already registered user: %s", stored_user.email)
            raise HTTPException(status_code=400,detail="User alredy registed")
        logger.info("User %s can be registered", stored_user.email)
        return user
    
async def validate_user_not_exists(session: Session, stored_user: User_registration):
    validator = Validation(session)
    await validator.registration(stored_user)
    logger.info("User validation passed for registration | create user: %s", stored_user.email)


async def insert_auth_record(session: Session, stored_user: User_registration, hashed_pass: str,user_role = None,status : bool | None = None):
    db_insert = DB_CRUD(session, UsersAuth,values= {
        "FullName": stored_user.FullName,
        "email": stored_user.email,
        "password": hashed_pass,
        "role" : user_role,
        "is_verified" : status
    })
    await db_insert.db_insert()
    logger.info("Inserting new auth record for user: %s", stored_user.email)

async def insert_business_record(session: Session, stored_user: User_registration,user_role,speciality : str | None = None):
    data = create_payload_user(stored_user)
    if not data:
        logger.error("Failed to create business record payload for user: %s", stored_user.email)
        raise HTTPException(status_code=404, detail="Missing data")
    adder = add_to_table(session, data,user_role,speciality)
    await adder.add_new_user()
    logger.info("The user has been successfully divided into tables: %s", stored_user.email)


async def after_registration(session: Session, stored_user: User_registration, hashed_pass: str):
    await validate_user_not_exists(session, stored_user)
    await insert_auth_record(session, stored_user, hashed_pass)
    await insert_business_record(session, stored_user,"Patient")
    logger.info("After registration process completed for user: %s", stored_user.email)

async def create_user(sessin : Session,stored_user,hashed_pass,user_role,speciality : str | None = None):
    await validate_user_not_exists(sessin,stored_user)
    await insert_auth_record(sessin,stored_user,hashed_pass,user_role,True)
    await insert_business_record(sessin,stored_user,user_role,speciality)
    logger.info("User created with role %s: %s", user_role, stored_user.email)

async def validate_user_and_issue_tokens(session: Session, stored_user: User_login):
    validator = Validation(session)
    user_data = await validator.login(stored_user)

    token_service = Token_servise()
    access_token = encrypt(token_service.create_access_token(user_data))
    refresh_token = encrypt(token_service.create_refresh_token(user_data))
    logger.info("Tokens issued for user: %s", stored_user.email)
    return user_data, access_token, refresh_token


async def sync_user_info_to_redis(user_data: dict):
    redis_key = f"email_info:{user_data['email']}"
    if not await r.exists(redis_key):
        logger.warning("User info not found in redis,adding new. User email: %s",user_data["email"])
        normalized_role = user_data["role"].value if hasattr(user_data["role"], "value") else str(user_data["role"])
        redis = RedisCRUD(redis_key)
        await redis.redis_hset({
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "role": normalized_role,
            "is_banned": str(user_data["is_banned"])
        })
        logger.info("User info added to redis. User email: %s",user_data["email"])


async def sync_refresh_token_to_redis_and_db(session: Session, user_data: dict, refresh_token: str):
    redis_key = f"email_refresh:{user_data['email']}"
    now = datetime.utcnow()
    expires = now + timedelta(days=jwt_settings.refresh_token_time)

    if await r.exists(redis_key):
        logger.info("Refresh token exists,updating. User email: %s",user_data["email"])
        await r.expire(redis_key, 60 * 24 * 3600)
        updater = DB_CRUD(session, Token_Storage,{"user_id": user_data["user_id"]},values= {
            "token": refresh_token,
            "created_at": now,
            "expires_at": expires
        })
        await updater.db_update()
        logger.info("Refresh token updated in database. User email: %s",user_data["email"])

    else:
        logger.info("Storing new refresh token. User email: %s",user_data["email"])
        redis = RedisCRUD(redis_key)
        await redis.redis_setex(60 * 24 * 3600,"is_active")
        inserter = DB_CRUD(session, Token_Storage,values= {
            "user_id": user_data["user_id"],
            "token_type": Token_type.Refresh_token,
            "token": refresh_token,
            "expires_at": expires
        })
        await inserter.db_insert()
        logger.info("Refresh token stored in database. User email: %s",user_data["email"])


async def after_login(session: Session, stored_user: User_login):
    user_data, access_token, refresh_token = await validate_user_and_issue_tokens(session, stored_user)
    await sync_user_info_to_redis(user_data)
    await sync_refresh_token_to_redis_and_db(session, user_data, refresh_token)
    logger.info("After login process completed for user: %s", stored_user.email)
    return access_token,refresh_token


async def validate_current_password(session : Session,password,email):

    db_select = DB_CRUD(session,UsersAuth,"email",email)
    result = await db_select.db_select()

    if not result:
        logger.warning("User not found for password validation: %s", email)
        raise HTTPException(status_code = 404,detail = "User not found")
    
    if not check_pass(result.password,password):
        logger.warning("Incorrect current password provided for user: %s", email)
        raise HTTPException(status_code = 401,detail = "Incorrect password")
    
    logger.info("Current password validated for user: %s", email)
    

async def after_change_pass(session : Session,user_password : Update_password,email):
    redis_key = f"email_pass:{email}"

    if await r.exists(redis_key):
        logger.info("Password change request already exists in redis for user: %s", email)
        raise HTTPException(status_code = 409,detail = "Please wait, you have already made a request")
    
    else:
        logger.info("Processing password change for user: %s", email)
        await validate_current_password(session,user_password.last_password,email)
    
    logger.info("Storing new hashed password temporarily in redis for user: %s", email)
    
    hashed_password = hash_pass(user_password.new_password)
    redis_setex = RedisCRUD(redis_key)
    await redis_setex.redis_setex(60*20,hashed_password)
    logger.info("New hashed password stored in redis for user: %s", email)

async def full_delete_user(session : Session,email):
    try:
      db_select = DB_CRUD(session,UsersAuth,"email",email)
      result = await db_select.db_select()

      if not result:
          logger.warning("User not found for deletion: %s", email)
          raise HTTPException(status_code = 404,detail = "User for delete not found")
          
      table = return_table(result.role)
      db_delete = DB_CRUD(session,Token_Storage,"user_id",result.id)
      await db_delete.db_delete()
      db_delete = DB_CRUD(session,table,"email",email)
      await db_delete.db_delete()
      db_delete = DB_CRUD(session,UsersAuth,"email",email)
      await db_delete.db_delete()
      redis_delete = RedisCRUD(f"email_info:{email}")
      await redis_delete.redis_delete()
      redis_delete = RedisCRUD(f"email_refresh:{email}")
      await redis_delete.redis_delete()
    except Exception as e:
        logger.exception("Error occurred while deleting user: %s | Error: %s", email, str(e))
        raise HTTPException(status_code = 500,detail = f"Delete failed{str(e)}")