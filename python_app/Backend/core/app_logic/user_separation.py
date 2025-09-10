from core.app_logic.rights_check import check_token
from models import Doctors,Admins,Locations,Patients,UsersRole
from core import logging_conf
from core.config.config_orm import Session
from core.app_logic.DB_command import DB_CRUD  
from sсhemas import User_registration
from fastapi import Depends,HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
logging_conf()

def create_payload_user(stored_user : User_registration):
    location_all = Locations(
        Country = stored_user.Country,
        City = stored_user.City,
        Region = stored_user.Region,
        AddressLine = stored_user.AddressLine
    )

    return {
        "FullName" : stored_user.FullName,
        "email" : stored_user.email,
        "Location" : location_all
        
    }
def return_table(user_role):
    table = {
            "Patient": Patients,
            "Doctor" : Doctors,
            "Admin" : Admins
        }
    role = table.get(user_role)
    if not role:
        logger.error("Invalid user role: %s", user_role)
        raise HTTPException(status_code=400, detail=f"Invalid role: {user_role}")
    logger.info("User role %s mapped to table %s", user_role, role.__name__)

    return role


async def send_table(session : Session,user = Depends(check_token)):
    if isinstance(user,JSONResponse):
        return user
    
    table = return_table(user["role"])
    email = user["email"]
    user = DB_CRUD(session,table,"email",email)
    result = await user.db_select()

    if not result:
        logger.error("User not found in database: %s", email)
        raise HTTPException(status_code=404,detail="User not found")
    logger.info("User %s found in database table %s", email, table.__name__)

    return {
        "user_id" : result.id,
        "email" : result.email,
        "role" : result.role,
        "table" : table.__name__
    }

class add_to_table():
    def __init__(self, session: Session, data, user_role, speciality: str | None = None):
        self.session = session
        self.data = data
        self.user_role = user_role
        self.speciality = speciality

    async def _create_location(self):
        location = self.data.pop("Location", None)
        if not location:
            logger.error("Location data is missing in user registration data")
            raise HTTPException(status_code=400, detail="Location data is required")

        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        logger.info("Location created with ID: %s", location.id)

        return location

    def _prepare_user_data(self, location_id: int):
        self.data["Location_id"] = location_id

        if self.user_role == UsersRole.Doctors:
            if not self.speciality:
                logger.warning("Speciality is missing for doctor registration")
                raise HTTPException(status_code=400, detail="Speciality is required for doctors")
            self.data["specialty"] = self.speciality
        logger.info("User data prepared for role %s", self.user_role)

        return self.data

    async def _create_user(self, role, user_data: dict):
        user_isinstall = role(**user_data)
        self.session.add(user_isinstall)

        await self.session.commit()
        await self.session.refresh(user_isinstall)
        logger.info("User created in table %s with ID: %s", role.__name__, user_isinstall.id)

        return user_isinstall

    async def add_new_user(self):
        role = return_table(self.user_role)
        if not role:
            logger.warning("Invalid user role provided: %s", self.user_role)
            raise HTTPException(status_code=400, detail=f"Invalid role: {self.user_role}")

        location = await self._create_location()

        user_data = self._prepare_user_data(location.id)
        logger.info("Adding new user with email: %s", user_data.get("email"))

        return await self._create_user(role, user_data)
