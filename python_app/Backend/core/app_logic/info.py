from core.config.config_orm import Session
from models import Banned_users
from core.app_logic.DB_command import DB_CRUD
from sqlalchemy import select
from sqlalchemy.orm import selectinload

class User_Info:
    def __init__(self, session: Session,main_table,output: list[str]):
        self.session = session
        self.main_table = main_table
        self.output = output

    async def miniman_info(self,offset : int = 0,limit : int = 10):
        query = select(self.main_table).offset(offset).limit(limit)
        result = await self.session.execute(query)
        records = result.scalars().all()

        return [
            {field: getattr(record, field) for field in self.output}
            for record in records
        ]

class Name_Full_Info(User_Info):
    def __init__(self,session: Session,main_table,join_table,main_fields: list[str],join_fields: list[str],user_id):
        super().__init__(session, main_table, main_fields)
        self.join_table = join_table
        self.join_fields = join_fields
        self.user_id = user_id

    async def name_full_info(self):
        stmt = (
            select(self.main_table)
            .filter(self.main_table.id == self.user_id)
            .options(selectinload(getattr(self.main_table, self.join_table)))
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
    
        
        return [
            {
                **{field: getattr(record, field) for field in self.output}, 
                self.join_table: [
                    {field: getattr(related, field) for field in self.join_fields}
                    for related in getattr(record, self.join_table)
                ]
            }
            for record in records
        ]
    
async def get_name(table_name,session,offset : int = 0,limit : int = 10):
   get_info = User_Info(
     session = session,
     main_table = table_name,
     output = ["FullName","id"]
   )

   return await get_info.miniman_info(offset=offset,limit=limit)

async def get_ban_staus(session : Session,banned_user_id):
    db_select = DB_CRUD(session,Banned_users,"banned_user_id",banned_user_id)
    result = await db_select.db_select()

    
    return {
        "reason" : result.reason,
        "expires_at" : result.expires_at,
        "is_active" : result.is_active
    }

    

    


