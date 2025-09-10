from core import check_token,set_cookie,Session,safe_decode_token,encrypt,r,Token_servise,logging_conf,load_user_to_redis,jwt_aes_settings as jwt_settings
from core.app_logic.DB_command import DB_CRUD
from core.app_logic.Redis_command import RedisCRUD
from models import Token_Storage
from fastapi import APIRouter,Depends,HTTPException,Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

async def select_to_db_for_token(session : Session,user_id):
    db_select = DB_CRUD(session,Token_Storage,"user_id",user_id)
    token = await db_select.db_select()

    if not token:
        logger.warning("Refresh token not found for user_id: %s", user_id)
        raise HTTPException(status_code = 404,detail = "Refresh token not found")
    
    logger.info("Refresh token found for user_id: %s", user_id)
    return token

@router.post("/new_access_token")
async def new_token(request : Request,session : Session,response : JSONResponse):


    token_servise = Token_servise()

    token = request.cookies.get(jwt_settings.refresh_token)

    if not token:
        logger.warning("Missing refresh_token in cookies")
        raise HTTPException(status_code = 404,detail = "Missing token")
    
    payload = safe_decode_token(token)

    email = payload.get("email")
    user_id = payload.get("user_id")

    key = f"email_info:{email}"
    
    get_redis_info = await r.get(f"email_refresh:{email}")

    if get_redis_info:
        logger.info("Refresh token found in redis for email: %s", email)
        ...

    else:
        logger.info("Refresh token not found in redis, try to select in db for email: %s",email)
        token = await select_to_db_for_token(session,user_id)

        safe_decode_token(token)
        
        redis = RedisCRUD(f"email_refresh:{email}")
        await redis.redis_setex(ttl=60*24*3600,value="is_active")
    
    get_redis_full_info = await r.hgetall(f"email_info:{email}")

    if get_redis_full_info:
        ...
    
    else:
        await load_user_to_redis(session,email)

    
    redis_hgetall = RedisCRUD(key)
    user = await redis_hgetall.redis_get_hashall()
        

    access_token = token_servise.create_access_token(user)
    encrypt_token = encrypt(access_token)
    response = JSONResponse(content={"message" : "new_access_token created"})
    set_cookie(response,"access_token",encrypt_token,60*15)
    logger.info("New access token created for user_id: %s",user_id)
    
    return response