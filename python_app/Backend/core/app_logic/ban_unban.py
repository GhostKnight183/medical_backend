from models import Banned_users,UsersAuth
from core import Session,logging_conf
from sсhemas import Ban_user
from sqlalchemy import select
from core.app_logic.DB_command import DB_CRUD
from core.app_logic.Redis_command import RedisCRUD
from fastapi import HTTPException
from datetime import datetime,timedelta
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
logging_conf()

class Unban():
    def __init__(self,session : Session,user_id):
        self.session = session
        self.user_id = user_id

    async def update_delete_bd(self,ban_id):
       db_delete_ban = DB_CRUD(self.session,Banned_users,"id",ban_id)
       db_update = DB_CRUD(self.session,UsersAuth,{"id" : self.user_id},values={"is_banned" : False})
       await db_delete_ban.db_delete()
       await db_update.db_update()
       logger.info("Database updated for unban. User ID: %s", self.user_id)
    
    async def get_ban_id_and_email(self):
       db_select = DB_CRUD(self.session,Banned_users,"banned_user_id",self.user_id)
       result_ban = await db_select.db_select()
       db_select = DB_CRUD(self.session,UsersAuth,"id",self.user_id)
       result_email = await db_select.db_select()
       
       if not result_ban:
          logger.warning("Attempt to unban a user who is not banned. User ID: %s", self.user_id)
          raise HTTPException(status_code = 404,detail="Banned user not found")
       
       logger.info("Banned user found. User ID: %s", self.user_id)
       return result_ban,result_email
        
    async def admin_unban(self):

     result_ban,result_email = await self.get_ban_id_and_email()
     email = result_email.email
     ban_id = result_ban.id

     await self.update_delete_bd(ban_id)
     redis_hset = RedisCRUD(f"email_info:{email}")
   
     await redis_hset.redis_hset(mapping={"is_banned" : "False"})
     logger.info("User unbanned. User ID: %s", self.user_id)
     return JSONResponse(content={"message": "User unbanned"})

    async def auto_unban(self):
      now = datetime.utcnow()
      result_ban,result_email = await self.get_ban_id_and_email()
 
      if result_ban.expires_at <= now:
         logger.info("Ban expired,try to auto-unban. User ID: %s", self.user_id)
         return await self.admin_unban()
      else:
         print(f"[AutoUnban] Ban still active. Expires: {result_ban.expires_at}, now: {now}")
         raise HTTPException(status_code=403, detail="You are banned")
     
      return None
      
async def add_new_ban(session : Session,email,user_id,admin_id,reason,expire):
   query = (select(Banned_users).filter(Banned_users.banned_user_id == user_id))
   user = await session.execute(query)
   result = user.scalars().first()

   if result:
     logger.warning("Attempt to ban an already banned user. User ID: %s", user_id)
     raise HTTPException(status_code=409, detail="User is already banned")
   
   db_update = DB_CRUD(session,UsersAuth,{"id" : user_id},{"is_banned" : True})
   await db_update.db_update()

   db_insert = DB_CRUD(session,Banned_users,values={"banned_user_id" : user_id,
                                                   "banned_by_id" : int(admin_id),
                                                   "reason" : reason,
                                                   "expires_at" : expire,
                                                   "is_active" : True})
   await db_insert.db_insert()
   logger.info("New ban added to database. User ID: %s", user_id) 

   #redis_hset = RedisCRUD(f"email_info:{email}")
   #
   #await redis_hset.redis_hset(mapping={"is_banned" : "true"})

async def new_ban(session : Session,user_id,categories : Ban_user,admin_id):
   now = datetime.utcnow()
   expires_at = now + timedelta(days=categories.ban_time)

   db_select = DB_CRUD(session,UsersAuth,"id",user_id)
   result = await db_select.db_select()
 
   if not result:
      logger.warning("Attempt to ban a non-existent user. User ID: %s", user_id)
      raise HTTPException(status_code = 404,detail = "User not found")

   await add_new_ban(session,result.email,user_id,admin_id,categories.reason,expires_at)

   return f" user banned until - {expires_at}\n reason - {categories.reason}"

