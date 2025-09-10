from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from models import Converstations, Messages
from sqlalchemy import select
from core import Session, logging_conf, r, safe_decode_token
from core.app_logic.Redis_command import RedisCRUD
from core.app_logic.DB_command import DB_CRUD
import logging
import json

logger = logging.getLogger(__name__)
logging_conf()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_key: str, websocket: WebSocket):
        if room_key not in self.active_connections:
            self.active_connections[room_key] = []
        self.active_connections[room_key].append(websocket)

    def disconnect(self, room_key: str, websocket: WebSocket):
        if room_key in self.active_connections:
            self.active_connections[room_key].remove(websocket)
            if not self.active_connections[room_key]:
                del self.active_connections[room_key]

    async def broadcast(self, room_key: str, message: dict):
        if room_key in self.active_connections:
            for connection in self.active_connections[room_key]:
                await connection.send_text(json.dumps(message))


manager = ConnectionManager()

async def add_new_room(session: Session, patient_id: int, doctor_id: int, key: str):
    db_insert = DB_CRUD(session, Converstations, values={
        "patient_id": patient_id,
        "doctor_id": doctor_id
    })
    new_room = await db_insert.db_insert()
    new_room_id = new_room.id

    redis_hset = RedisCRUD(key)
    await redis_hset.redis_hset({
        "room_id": new_room_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id
    })
    logger.info("Created new conversation doctor=%s patient=%s", doctor_id, patient_id)

    return new_room_id


async def check_root_for_room(session: Session, doctor_id: int, patient_id: int):
    key = f"room:patient_id:{patient_id}doctor_id:{doctor_id}"

    result = await r.hgetall(key)
    if result:
        logger.warning("Room already exists in Redis doctor=%s patient=%s", doctor_id, patient_id)
        raise HTTPException(status_code=409, detail="Room already exists")

    query = select(Converstations).filter(
        Converstations.patient_id == patient_id,
        Converstations.doctor_id == doctor_id
    )
    result = (await session.execute(query)).scalars().first()

    if result:
        redis_set = RedisCRUD(key)
        await redis_set.redis_hset({
            "room_id": result.id,
            "patient_id": patient_id,
            "doctor_id": doctor_id
        })
        logger.warning("Room already exists in DB doctor=%s patient=%s", doctor_id, patient_id)
        raise HTTPException(status_code=409, detail="Room already exists")

    room_id = await add_new_room(session, patient_id, doctor_id, key)
    return room_id, key



async def add_new_message(session: Session, converstation_id , sender_id, recipient_id, content):
    db_insert = DB_CRUD(session, Messages, values={
        "converstation_id": converstation_id,
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "content": content
    })
    await db_insert.db_insert()
    logger.info("message from sender_id: %s recipient_id: %s added to db", sender_id, recipient_id)


async def new_message(session: Session, patient_id, doctor_id, sender_id, recipient_id, content):
    redis = await r.hgetall(f"room:patient_id:{patient_id}doctor_id:{doctor_id}")
    redis_dict = {k.decode(): v.decode() for k, v in redis.items()}
    room_id = redis_dict.get("room_id")

    if redis:
        logger.info("Room_id: %s found, saving message", room_id)
        await add_new_message(session, room_id, sender_id, recipient_id, content)
    else:
        logger.warning("Room not found, trying to find room in DB")
        await check_root_for_room(session, doctor_id, patient_id)

    return None


async def validation_users_for_chat(websocket: WebSocket, session: Session, patient_id: str, doctor_id: str):
    token = websocket.cookies.get("access_token")
    if not token:
        logger.warning("Missing token")
        await websocket.close(code=1008)
        raise HTTPException(status_code=1008, detail="Missing token")

    key = f"room:patient_id:{patient_id}doctor_id:{doctor_id}"
    redis = RedisCRUD(key)
    result = await redis.redis_get_hashall()

    if not result:
        logger.warning("Room not found in Redis, checking DB")
        try:
            await check_root_for_room(session, doctor_id, patient_id)
            result = await redis.redis_get_hashall()
        except HTTPException as e:
            await websocket.close(code=e.status_code)
            raise

    payload = safe_decode_token(token)
    user_id = payload.get("user_id")

    if user_id not in [result["patient_id"], result["doctor_id"]]:
        logger.warning("User %s not authorized for room %s", user_id, result["room_id"])
        await websocket.close(code=1003)
        raise HTTPException(status_code=1003, detail="User not authorized in room")

    logger.info("User %s validated for room %s", user_id, result["room_id"])
    return user_id


async def websocket_chat_handler(websocket: WebSocket, session: Session, patient_id: str, doctor_id: str):
    key = f"room:patient_id:{patient_id}doctor_id:{doctor_id}"

    try:
        user_id = await validation_users_for_chat(websocket, session, patient_id, doctor_id)
        await websocket.accept()

        await manager.connect(key, websocket)
        logger.info("User %s connected to room %s", user_id, key)

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            content = payload.get("content")
            recipient_id = payload.get("recipient_id")

            if not content or not recipient_id:
                await websocket.send_text(json.dumps({"error": "Missing content or recipient_id"}))
                continue

            await new_message(
                session,
                patient_id,
                doctor_id,
                sender_id=user_id,
                recipient_id=recipient_id,
                content=content
            )

            await manager.broadcast(key, {
                "status": "message_sent",
                "from": user_id,
                "to": recipient_id,
                "message": content
            })

    except WebSocketDisconnect:
        manager.disconnect(key, websocket)
        logger.info("User %s disconnected from room %s", user_id, key)

    except Exception as e:
        logger.error("WebSocket error: %s", str(e))
        await websocket.close(code=1011)
        manager.disconnect(key, websocket)

async def return_chat(current_user_id,converstation_id ,session : Session,offset : int = 0,limit : int = 10):
    query = (select(Messages).filter(Messages.converstation_id == int(converstation_id)).
             order_by(Messages.created_at.desc()).offset(offset).limit(limit))

    messages = await session.execute(query)

    result = messages.scalars().all()

    if not result:
        logger.warning("Message in room: %s not found",converstation_id)
        raise HTTPException(status_code = 404,detail = "Message not found in room")

    return [{
       "content" : message.content,
       "created_at" :  message.created_at,
       "is_mine" : message.sender_id == current_user_id
    }
    for message in result
    ]