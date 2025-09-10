from core.config.jwt_aes_config import jwt_aes_settings as jwt_settings
from fastapi import HTTPException
from datetime import timedelta
import datetime
import jwt

class Token_servise():
    def __init__(self):
        self.private_key = jwt_settings.private_key.read_text()
        self.public_key = jwt_settings.public_key.read_text()
        self.algorithm = jwt_settings.algorithm
        self.email_token_time = timedelta(minutes = jwt_settings.email_token_time)
        self.access_token_time = timedelta(minutes = jwt_settings.access_token_time)
        self.refresh_token_time = timedelta(days = jwt_settings.refresh_token_time)

    def create_token(self,payload : dict,exp: datetime):
        now = datetime.datetime.utcnow()
        payload.update({
            "iat" : now,
            "exp" : exp
        })
        return jwt.encode(
            payload,
            self.private_key,
            algorithm = self.algorithm
        )
    
    def decode_token(self,token : str):
        return jwt.decode(
            token,
            self.public_key,
            algorithms = self.algorithm
        )
    
    def create_access_token(self,stored_user : dict):		
        return self.create_token(
            payload={
                "token_type" : jwt_settings.access_token,
                "sub" :  str(stored_user["user_id"]),
                "email" : stored_user["email"],
                "role" : stored_user["role"],
                "is_banned" : stored_user["is_banned"]

            },
            exp = datetime.datetime.utcnow() + self.access_token_time
        )
    def create_refresh_token(self,stored_user : dict):
        if "email" not in stored_user or "role" not in stored_user:
            raise HTTPException(status_code= 404,detail="NotFound")    
        return self.create_token(
            payload={
                "token_type" : jwt_settings.refresh_token,
                "sub" : str(stored_user["user_id"]),
                "email" : stored_user["email"],
                "role" : stored_user["role"]
            },
            exp = datetime.datetime.utcnow() + self.refresh_token_time
        )
    
    def create_email_token(self,stored_user : dict,token_type):
        return self.create_token(
            payload = {
                "token_type" : token_type,
                "email" : stored_user["email"]
            },
            exp = datetime.datetime.utcnow() + self.email_token_time 
              )