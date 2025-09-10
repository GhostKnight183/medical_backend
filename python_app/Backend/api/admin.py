from fastapi import APIRouter,Depends,HTTPException
from core import Session,Role_checker,User_Info,full_delete_user,Unban,send_table,new_ban,create_user,logging_conf
from core.security.utils import hash_pass
from datetime import timedelta
from sсhemas import Ban_user,User_registration
from models import UsersAuth,UsersRole as Role
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

@router.post("/create_user")
async def create_user_(user_role : Role,stored_user : User_registration,session : Session):
   
      hashed_pass = hash_pass(stored_user.password)
      if user_role in [Role.Doctors]:
           await create_user(session,stored_user,hashed_pass,user_role,stored_user.specialty)
      
      else:
           await create_user(session,stored_user,hashed_pass,user_role)

      logger.info("New user created with role: %s", user_role)
      return f"{user_role},was created"
    

@router.get("/check_all_user_info")
async def all_user(sesion : Session,offset : int = 0,limit : int = 10,depens = Depends(Role_checker(["Admin"]))):
      user_info = User_Info(
            session=sesion,
            main_table=UsersAuth,
            output=["id","FullName","email","role","is_banned"]
      )
      logger.info("All users info retrieved")
      return await user_info.miniman_info(offset=offset,limit=limit)

@router.delete("/delete_user/{email}")
async def delete_user(session : Session,email : str,depents = Depends(Role_checker(["Admin"]))):
      await full_delete_user(session,email)

      return {"message":"user_delete"}


@router.patch("/ban_user/{banned_id}")
async def ban(session : Session,banned_id : int,categories : Ban_user,admin_id = Depends(send_table),depens = Depends(Role_checker(["Admin"]))):
      

      if categories.ban_time <= 0:
            logger.warning("Attempt to ban user with non-positive ban time: %s", categories.ban_time)
            raise HTTPException(status_code = 422,detail = "ban time must be greater than 0")
      
      ban_result = await new_ban(session,banned_id,categories,admin_id["user_id"])
      logger.info("User with id %d banned by admin with id %d for %s", banned_id, admin_id["user_id"], categories.ban_time)   
      return ban_result

@router.patch("/unban_user/{user_id}")
async def unban_user(session : Session,user_id : int,depends = Depends(Role_checker(["Admin"]))):
      await Unban(session,user_id).admin_unban()

      return {"message":"user unban"}