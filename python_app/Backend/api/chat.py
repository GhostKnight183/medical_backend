from fastapi import APIRouter,Depends,WebSocket
from core import (check_root_for_room,websocket_chat_handler,
                  Role_checker,Session,send_table,logging_conf,return_chat)
from models import Converstations
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

@router.post("/create_new_room/{patient_id}")
async def new_room(session : Session,patient_id : int,user = Depends(send_table),depens = Depends(Role_checker(["Doctor"]))):

    room_id,key = await check_root_for_room(session,user["user_id"],patient_id)
    
    logger.info("Room: %s created passed",room_id)

    return room_id,key

@router.websocket("/chat/{patient_id}/{doctor_id}")
async def medical_chat(websocket : WebSocket,session : Session,patient_id,doctor_id):

    await websocket_chat_handler(websocket,session,patient_id,doctor_id)

    logger.info("message processed successfully")

@router.get("/my_rooms/{doctor_id}")
async def get_rooms(session : Session,doctor_id,offset,limit):

    query = await session.execute(select(Converstations).filter(Converstations.doctor_id == int(doctor_id)).offset(offset).limit(limit))

    rooms = query.scalars().all()


    return [{
        "room_id" : room.id,
        "patient_id" : room.patient_id,
        "doctor_id" : room.doctor_id
    }
    for room in rooms
    ]

@router.get("/my_room/{patient_id}")
async def get_my_room(session : Session,patient_id):

    query = await session.execute(select(Converstations).filter(Converstations.patient_id == int(patient_id)))

    room = query.scalars().first()

    logger.info("Room : %s for patient returned",room.id)

    return {"room_id": room.id,
            "patient_id": room.patient_id,
            "doctor_id": room.doctor_id}

@router.get("/return_chat/{user_id}/{room_id}")
async def chat(user_id,room_id,session : Session,offset = 0,limit = 10):
    result_chat = await return_chat(user_id,room_id,session,offset,limit)

    logger.info("Messages: %s in room: %s returned",result_chat["content"],room_id)

    return result_chat