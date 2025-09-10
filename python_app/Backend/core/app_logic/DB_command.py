from sqlalchemy import select, update, delete
from core import Session,logging_conf
import logging

logger = logging.getLogger(__name__)
logging_conf()

class DBError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

async def safe_db_call(func, *args, not_found_msg=None, **kwargs):
    try:
        result = await func(*args, **kwargs)
        if result is None and not_found_msg:
            logger.warning(not_found_msg)
            raise DBError(not_found_msg, status_code=404)
        return result
    except Exception as e:
        logger.exception("Database operation failed: %s", str(e))
        raise DBError(f"DB operation failed: {str(e)}")
logger.info("Database operation succeeded")

class DB_CRUD:
    def __init__(self, session: Session, table_name, parameter=None, values=None):
        self.session = session
        self.table_name = table_name
        self.parameter = parameter
        self.values = values

    @staticmethod
    def resolve_field(table_name, parameter):
        field = getattr(table_name, parameter, None)
        if field is None:
            logger.error("Invalid parameter: %s for table: %s", parameter, table_name.__name__)
            raise DBError(f"Invalid parameter: {parameter}", status_code=400)
        
        return field

    async def db_select(self, all: bool = False):
        field = self.resolve_field(self.table_name, self.parameter)
        query = select(self.table_name).where(field == self.values)
        result = await safe_db_call(self.session.execute, query)
    
        records = result.scalars()
        if all:
            data = records.all()
            if not data:
                logger.warning("No records found for %s = %s", self.parameter, self.values)
                raise DBError("No records found", status_code=404)
            return data
        else:
            record = records.first()
            if not record:
                logger.warning("Record not found for %s = %s", self.parameter, self.values)
                raise DBError("Record not found", status_code=404)
            
        return record
 
    async def db_delete(self):
        field = self.resolve_field(self.table_name, self.parameter)
        query = delete(self.table_name).where(field == self.values)
        result = await safe_db_call(self.session.execute, query)
        await safe_db_call(self.session.commit)
        if result.rowcount == 0:
            logger.warning("Record to delete not found for %s = %s", self.parameter, self.values)
            raise DBError("Record not found", status_code=404)
        
        return {"message": "Record deleted successfully"}

    async def db_insert(self):
        new_record = self.table_name(**self.values)
        self.session.add(new_record)
        await safe_db_call(self.session.commit)
        await safe_db_call(self.session.refresh, new_record)

        return new_record

    async def db_update(self):
        conditions = []
        for key, val in self.parameter.items():
            field = self.resolve_field(self.table_name, key)
            conditions.append(field == val)
        query = update(self.table_name).where(*conditions).values(**self.values)
        result = await safe_db_call(self.session.execute, query)
        await safe_db_call(self.session.commit)
        if result.rowcount == 0:
            logger.warning("Record to update not found for conditions: %s", self.parameter)
            raise DBError("Record not found", status_code=404)
        
        return {"message": "Record updated successfully"}