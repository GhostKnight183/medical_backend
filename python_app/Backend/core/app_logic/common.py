from core import Path,send_email,full_delete_user,jwt_aes_settings as jwt_settings,Session,return_table,r,DB_CRUD,Token_servise,RedisCRUD,logging_conf
from models import UsersAuth,Grades,Diagnoses
from fastapi import HTTPException,APIRouter,Request
from sqlalchemy import select
from fastapi.templating import Jinja2Templates
from datetime import datetime,timedelta
import jwt
import logging

logger = logging.getLogger(__name__)
logging_conf()

router = APIRouter()

BASE_DIR = Path(__file__).parent

templates = Jinja2Templates(directory=Path("python_app/Frontend/email"))


async def html_for_email(html_template: str, api,subject,email,token):

    if not token or not email:
        logger.error("No token or email provided for sending email")
        raise HTTPException(status_code=404,detail="Not token or email")
     
    template_path = Path(f"python_app/Frontend/email{html_template}").read_text(encoding="utf-8")
    link = f"http://localhost/api/v1/{api}?token={token}"
    html_content = template_path.replace("{{link}}",link)
     
    await send_email(
         recipient = email,
         subject = subject,
         content = html_content
 
    )
    logger.info("Email sent to %s for %s", email, subject)


def validate_token(request : Request,token_type,title,success_message):
    error_message = "There was a server-side error or your session has expired"
    token_servise = Token_servise()
    token = request.query_params.get("token")

    if not token:
        logger.error("Token not found in request")
        raise HTTPException(status_code=404,detail="token not found")
    try:
        payload = token_servise.decode_token(token)
        

        if not payload:
            logger.error("Invalid Token payload")
            raise HTTPException(status_code=401,detail="Invalid Token payload")
        
        email = payload.get("email")
        
        if payload.get("token_type") == token_type:
            logger.info("Token validation passed. Token type: %s", token_type)
            return email,templates.TemplateResponse(
                    "confirmation_page.html",
                 {
                     "request" : request,
                     "title" : title,
                     "message" : success_message,
                     "color" : "#28a745",
                     "success" : True
                 }
            )
            

        else:
            logger.warning("Invalid token_type: %s", payload.get("token_type"))
            raise HTTPException(status_code=401,detail="Invalid token_type")
    
    except (jwt.ExpiredSignatureError,jwt.InvalidTokenError):
         logger.warning("Token error: Expired or Invalid token")
         return None,templates.TemplateResponse(
                "confirmation_page.html",
            {
                "request" : request,
                "title" : title,
                "message" : error_message,
                "color" : "#dc3545",
                "success" : False
            }

        )
logger.info("Validate token function completed")      

@router.get("/verified_email")
async def verified_email(request : Request,session : Session):
    email,response =  validate_token(
        request = request,
        token_type = jwt_settings.verified_email_token,
        title = "Verified Email",
        success_message = "Your email address has been successfully verified.",
      ) 
    if email:
        db_update = DB_CRUD(session,UsersAuth,{"email": email},{"is_verified": True})
        await db_update.db_update()
        logger.info("User email status updated to verified in database for user: %s", email)
  
    return response

@router.get("/delete_account")
async def delete_my_account(request : Request,session : Session):
    email,response =  validate_token(
        request = request,
        token_type = jwt_settings.delete_account_token,
        title = "Delete Account",
        success_message = "Your account has been successfully deleted.",
      ) 
    if email:
        await full_delete_user(session,email)
        logger.info("Account successfully deleted for user: %s", email)
        
    return response

@router.get("/change_password")
async def change_password(request : Request,session : Session):
    email,response = validate_token(
        request = request,
        token_type = jwt_settings.change_pass_token,
        title = "Change Password",
        success_message = "your password has been successfully changed"
    )
    if email:
        hashed_password = await r.get(f"email_pass:{email}")
        db_update = DB_CRUD(session,UsersAuth,{"email": email},{"password": hashed_password})
        await db_update.db_update()
        redis_delete = RedisCRUD(f"email_pass:{email}")
        await redis_delete.redis_delete()
        logger.info("Temporary password removed from Redis for user: %s", email)
    
    return response

async def check_root_for_grades(session : Session,patients_id,doctor_id):
    query = await session.execute(select(Grades).filter(Grades.patient_id == patients_id,Grades.doctor_id == doctor_id))
    result = query.scalars().first()

    if result:
        logger.warning("Patient: %s alredy have grades for doctor: %s",patients_id,doctor_id)
        raise HTTPException(status_code = 400,detail = "You alredy have grades for this doctor")
    
    query = await session.execute(select(Diagnoses).filter(Diagnoses.patient_id == patients_id,Diagnoses.doctor_id == doctor_id))
    result = query.scalars().first()

    if not result:
        logger.warning("Patient: %s don't have diagnose at doctor: %s",patients_id,doctor_id)
        raise HTTPException(status_code = 403,detail = "You cannot leave a review until treatment is completed.")
    
    return True
async def get_grades(session : Session,doctor_id):
      fiften_days_ago = datetime.utcnow() - timedelta(days=15)
      query = await session.execute(select(Grades).filter(Grades.doctor_id == doctor_id,Grades.created_at >= fiften_days_ago))

      grades = query.scalars().all()

      if not grades:
          logger.warning("Grades for doctor: %s not found",doctor_id)
          raise HTTPException(status_code = 404,detail = "Grades not found")

      average = calculator_average(grades)
 
      return average  

def calculator_average(grades : list[Grades]):
    if not grades:
        return 0.0
    total = sum(g.stars for g in grades)
    return round(total / len(grades), 2)
