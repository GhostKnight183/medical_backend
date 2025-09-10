from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from fastapi import Depends
from typing import Annotated
from core import setting

async_engine = create_async_engine(
    setting.DB_asyncpg, 
    pool_size=33,           
    max_overflow=36,        
    pool_timeout=60,
    pool_recycle=1800)

async_sessionmaker = async_sessionmaker(async_engine,class_=AsyncSession)

async def get_db_session():
    async with async_sessionmaker() as session:
        yield session
        await session.commit()


Session = Annotated[AsyncSession,Depends(get_db_session)]