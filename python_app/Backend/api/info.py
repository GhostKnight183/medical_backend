from fastapi import APIRouter,Depends
from models import Doctors,Patients
from core import Session,send_table,get_name,Name_Full_Info,check_token,get_ban_staus,logging_conf,get_grades
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

@router.get("/check_my_grade/{doctor_id}")
async def name_and_grade(doctor_id : int,session : Session):
   grade = await get_grades(session,doctor_id)

   return grade

@router.get("/name_and_diagnoses/{patient_id}")
async def name_and_diagnoses(patient_id : int,session : Session):

    name_full_info = Name_Full_Info(
    session=session,
    main_table = Patients,
    join_table = "diagnoses",
    main_fields = ["FullName"],
    join_fields = ["diagnoses", "description", "recommendations"],
    user_id = patient_id
) 
    get_info = await name_full_info.name_full_info()
    logging.info("Name and diagnoses info retrieved for patient_id: %d", patient_id)
    return get_info

@router.get("/ban_status")
async def status(session : Session,user_id = Depends(check_token)):
   
   return await get_ban_staus(session,user_id["user_id"])


@router.get("/give_the_role")
def user_role(user = Depends(send_table)):
    return user