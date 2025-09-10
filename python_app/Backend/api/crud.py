from fastapi import APIRouter,Depends,Request
from fastapi.responses import JSONResponse
from core import (Session,hash_pass,after_registration,after_login,after_change_pass,
                  html_for_email,Token_servise,set_cookie,Role_checker,check_token,validate_current_password,logging_conf,
                  jwt_aes_settings as jwt_settings)
from sсhemas import User_registration,User_login,Update_password
from slowapi.util import get_remote_address
from slowapi import Limiter
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

limiter = Limiter(key_func= get_remote_address)

@router.post("/registration")
@limiter.limit("2/hour")
async def registrations(request : Request,
                        session : Session,
                        stored_user : User_registration):
    
    hashed_pas = hash_pass(stored_user.password)
    
    await after_registration(session,stored_user,hashed_pas)

    logger.info("Registration passed for user: %s ",stored_user.FullName)
    return stored_user

@router.post("/send_verified_email")
async def verified_my_email(stored_user : User_registration):

    token_servise = Token_servise()

    user_dict = stored_user.dict()

    user_dict.update({
        "role" : "Patient"
    })
    token = token_servise.create_email_token(user_dict,jwt_settings.verified_email_token)
 
    await html_for_email(
        html_template = "/send_email_verification.html",
        api = "verified_email",
        subject = "verified_email",
        email = stored_user.email,
        token = token
    )
    logger.info("Verified message send to: %s",stored_user.email)

    return {"message" : "we sent a message to your email"}

@router.post("/login")
@limiter.limit("3/minute")
async def user_login(stored_user : User_login,
                     session : Session,
                     request : Request):
    
    encrypt_access_token,encrypt_refresh_token = await after_login(session,stored_user)

    response = JSONResponse(content={"message" : "Login succefull"})
    set_cookie(response,jwt_settings.refresh_token,encrypt_refresh_token,60*30*3600)
    set_cookie(response,jwt_settings.access_token,encrypt_access_token,60*15)
    
    logger.info("Login passed for user: %s",stored_user.email)
    return response

@router.patch("/new_password")
async def change_password(user_password : Update_password,session : Session,depens = Depends(Role_checker(["Patient","Doctor"]))):
    token_servise = Token_servise()

    await after_change_pass(session,user_password,depens["email"])

    token = token_servise.create_email_token(depens,jwt_settings.change_pass_token)

    await html_for_email(
        html_template = "/send_email_change_password.html",
        api = "change_password",
        subject = "Change Password",
        email = depens["email"],
        token = token
    )
    logger.info("Change password passed,email sent to: %s",depens["email"])
    return {"message" : "we sent a message to your email"}

@router.delete("/delete_my_account")
async def delete_account(password : str,session : Session,user_data = Depends(check_token)):
      token_servise = Token_servise()

      await validate_current_password(session,password,user_data["email"])

      token = token_servise.create_email_token(user_data,jwt_settings.delete_account_token)

      await html_for_email(
          html_template = "/send_email_delete_account.html",
          api = "delete_account",
          subject = "delete_account",
          email = user_data["email"],
          token = token
      )
      logger.info("Delete account passed,email sent to: %s",user_data["email"])
      return {"message" : "we sent a message to your email"}

@router.post("/logout")
def logout_user():
    response = JSONResponse(content={"message":"Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response