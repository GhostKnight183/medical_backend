from fastapi import APIRouter,Depends,HTTPException
from core import Session,Role_checker,DB_CRUD,send_table,logging_conf
from sсhemas import Diagnose
from models import Patients_Requests,RequestStatus,Diagnoses
from sqlalchemy import select
import datetime
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

@router.patch("/accept_request/{request_id}")
async def accept_request(request_id,session : Session,depens = Depends(Role_checker(["Doctor"]))):
    now = datetime.datetime.utcnow()

    db_update = DB_CRUD(session,Patients_Requests,{"id" : int(request_id)},values={"status" : RequestStatus.accepted,"confirmed_at" : now})

    await db_update.db_update()
    logger.info("Request with id %d accepted", request_id)

    return {"message" : "Request Accept"}


@router.get("/check_my_request")
async def check_request(session : Session,offset : int = 0,limit : int = 10,doctor_id = Depends(send_table),depents = Depends(Role_checker(["Doctor"]))):

    query = await session.execute(select(Patients_Requests).filter(Patients_Requests.doctor_id == doctor_id["user_id"]).offset(offset).limit(limit))

    result = query.scalars().all()

    if not result:
        logger.info("Doctor: %s don't have request",doctor_id["user_id"])
        raise HTTPException(status_code = 200,detail = "You don't have request")

    logger.info("Requests retrieved for doctor_id: %s", doctor_id["user_id"])

    return [{
        "id" : request.id,
        "requested_at" : request.requested_at,
        "status" : request.status,
        "patient_id" : request.patient_id
    }
    for request in result
    ]

@router.post("/patient_diagnose/{request_id}")
async def patient_diagnose(session : Session,request_id : int,diagnose : Diagnose,doctor_id = Depends(send_table),depens = Depends(Role_checker(["Doctor"]))):

    db_select = DB_CRUD(session,Patients_Requests,"id",request_id)
    result = await db_select.db_select()

    db_insert = DB_CRUD(session,Diagnoses,values={"patient_id" : result.patient_id,
                                                
                                        "doctor_id" : doctor_id["user_id"],
                                        "request_id" : request_id,
                                        "diagnoses" : diagnose.diagnoses,
                                        "description" : diagnose.description,
                                        "recommendations" : diagnose.recommendations
                                        })
    await db_insert.db_insert()
    logger.info("Diagnosis made for request_id: %d by doctor_id: %s", request_id, doctor_id["user_id"])
    
    return {"message" : "diagnosis made"}
