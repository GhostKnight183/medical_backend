import logging
from core import Session,Unban,Token_servise,r,logging_conf
from core.app_logic.DB_command import DB_CRUD
from core.app_logic.Redis_command import RedisCRUD
from core.security.utils import decrypt
from fastapi import Depends,Request,HTTPException
from models import UsersAuth
import jwt

logger = logging.getLogger(__name__)
logging_conf()

def validation_payload(redis_dict: dict, token_dict: dict) -> bool:
    for key, value in redis_dict.items():
        decoded_key = key.decode()
        if decoded_key not in token_dict.keys():
            continue 

        decoded_value = value.decode()
        token_value = str(token_dict[decoded_key])

        if decoded_value != token_value:
            logger.warning("Mismatch for key=%s: redis=%s token=%s", decoded_key, decoded_value, token_value)
            return False
    logger.info("Payload validation passed")
    return True

def safe_decode_token(token):
    token_servise = Token_servise()
    try:
        decrypt_token = decrypt(token)
        decode_token = token_servise.decode_token(decrypt_token)

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=401,detail="Session Expired")
        
    except jwt.InvalidTokenError:
        logger.warning("Invalid token payload")
        raise HTTPException(status_code=401,detail="Invalid token payload")
    
    except Exception as e:
        logger.exception("Unexpected error while decoding token")
        raise HTTPException(status_code = 500,detail = f"Decode token Failed{str(e)}")
    
    logger.info("Safe decode token passed")
    return decode_token

def validate_token_format(token):

    if not isinstance(token, str) or not token.isascii():
       logger.warning("Malformed token")
       raise HTTPException(status_code=400, detail="Malformed token")
    
    if len(token) > 8000:
       logger.warning("Token too large. Token_length : %s",len(token))
       raise HTTPException(status_code=400, detail="Token too large")
    
    if len(set(token)) < 10:
       logger.warning("Token entropy too low")
       raise HTTPException(status_code=400, detail="Token entropy too low")
    
    logger.info("Validate token formate passed")

async def load_user_to_redis(session : Session,email):
    db_select = DB_CRUD(session,UsersAuth,"email",email)
    result = await db_select.db_select()

    if result:
        logger.info("User found in db. User email : %s",email)
        redis = RedisCRUD(f"email_info:{result.email}")
        await redis.redis_hset(mapping= {"user_id" : str(result.id),
                                        "email" : result.email,
                                        "role" : result.role,
                                        "is_banned" : str(result.is_banned)})
    else:
        logger.warning("User not found in db. User email: %s",email)
        raise HTTPException(status_code = 404,detail = "User not found")
    
    logger.info("load user to redis passed")


async def check_token(request: Request, session: Session):
    token = request.cookies.get("access_token")

    if not token:
        logger.warning("User don't have token")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    validate_token_format(token)

    payload = safe_decode_token(token)

    email = payload.get("email")

    is_banned = payload.get("is_banned")

    if not email :
        logger.error("Invalid token payload")
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    if await r.exists(f"email_info:{email}"):
        logger.info("User found in redis. User email: %s",email)
        redis_info = await r.hgetall(f"email_info:{email}")

        if not validation_payload(redis_info,payload):
            logger.warning("Token payload mismatch. User email: %s", email)
            raise HTTPException(status_code = 401,detail = "Unauthorized")
    
    else:
        logger.info("User not found in redis,try to select in db. User email: %s",email)
        await load_user_to_redis(session,email)
    
    updated_redis_info = await r.hgetall(f"email_info:{email}")
    decoded_items = {key.decode() : value.decode() for key,value in updated_redis_info.items()}

    if is_banned == True:
       logger.info("User banning try to unban")
       response = await Unban(session,int(decoded_items["user_id"])).auto_unban()
       if response:
           return response
    
    logger.info("Right check user passed. User email: %s",email)
    return {
        "user_id": int(decoded_items["user_id"]),
        "email": decoded_items["email"],
        "role": decoded_items["role"],
        "is_banned": decoded_items["is_banned"]
    }
    
def Role_checker(allowed_roles: list[str]):
    async def checker(user = Depends(check_token)):
        if user["role"] not in allowed_roles:
            logger.warning("User role : %s not found in allowed roled: %s",user["role"],allowed_roles)
            raise HTTPException(status_code=403, detail="Forbidden")
        
        logger.info("Access granted: role=%s matched in allowed_roles=%s",user["role"], allowed_roles)
        return user
    return checker



