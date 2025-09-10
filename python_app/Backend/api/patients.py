from fastapi import APIRouter,Depends,HTTPException
from core import Session,Role_checker,send_table,DB_CRUD,logging_conf,check_root_for_grades
from sqlalchemy import select
from models import Patients_Requests,Doctors,SpecialtyEnum,Grades
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

@router.get("/sorted_specialty")
async def sort(specialty : SpecialtyEnum,session : Session,offset = 0,limit = 10):
     
     query = await session.execute(select(Doctors).filter(Doctors.specialty == specialty).offset(offset).limit(10))
     
     result = query.scalars().all()
     specialty_all = [{
         "doctor_id" : doctor.id,
          "FullName" : doctor.FullName,
          "specialty" : doctor.specialty
     }
     for doctor in result
     ]
     logger.info("Sorted doctors retrieved for specialty: %s", specialty)
     return specialty_all

@router.post("/send_requests/{doctor_id}")
async def requests(session : Session,doctor_id,user = Depends(send_table),depends = Depends(Role_checker(["Patient"]))):
    
    if not user or not doctor_id: 
        logger.warning("User or doctor_id not found")
        raise HTTPException(status_code=404,detail="Not found")
    
    new_requests = DB_CRUD(session,Patients_Requests,values={"patient_id":user["user_id"],"doctor_id":int(doctor_id)})
    result = await new_requests.db_insert()
    logger.info("New request created with id: %s", result.id)

    return result.id

@router.post("/new_grades/{doctor_id}/{grades}")
async def doctor_grade(session : Session,doctor_id : int,grades : float,user = Depends(send_table),depens = Depends(Role_checker(["Patient"]))):
    
    await check_root_for_grades(session,user["user_id"],doctor_id)
    db_insert = DB_CRUD(session,Grades,values={"patient_id" : user["user_id"],
                                               "doctor_id" : doctor_id,
                                               "stars" : grades})
    await db_insert.db_insert()

    logger.info("The grade was successfully given to the doctor: %s by the patient: %s",doctor_id,user["user_id"])

    return {"message" : "The grade was successfully given to the doctor"}
