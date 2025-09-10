from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from core import async_engine,email_router,DBError,RedisError,logging_conf
from api import (crud_router,new_access_token_router,doctor_router,
                patients_router,admin_router,info_router,chat_router)
from models import Base
from core import r
import logging
import uvicorn

app = FastAPI()

logger = logging.getLogger(__name__)
logging_conf()

@app.on_event("startup")
async def startup():
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database connected and tables created successfully")
    except Exception as e:
        logger.critical("Failed to connect to the database: %s", str(e))

@app.exception_handler(DBError)
async def db_error_handler(request: Request, exc: DBError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

@app.exception_handler(RedisError)
async def redis_error_handler(request: Request, exc: RedisError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

app.include_router(crud_router,prefix="/api/v1",tags=["Account"])
app.include_router(patients_router,prefix="/api/v1",tags=["Full Patient Router"])
app.include_router(doctor_router,prefix = "/api/v1",tags=["Full Doctor Router"])
app.include_router(info_router,prefix = "/api/v1",tags=["Information for all role"])
app.include_router(admin_router,prefix="/api/v1",tags=["Full Admin Router"])
app.include_router(chat_router,prefix="/api/v1",tags=["Full Chat Router"])
app.include_router(email_router,prefix="/api/v1",tags=["Auto Email(Don't Tuch)"])
app.include_router(new_access_token_router,prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("main:app",host="0.0.0.0",port=8000)
