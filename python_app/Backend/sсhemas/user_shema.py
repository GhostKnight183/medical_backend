from pydantic import BaseModel,Field,EmailStr
from typing import Annotated,Optional


class User_registration(BaseModel):
    FullName : str = Field(max_length=45)
    email : Annotated[str,EmailStr]
    password: Optional[str] = Field(None, min_length=6, max_length=15)
    Country : str
    City : str
    Region : str
    AddressLine : str
    specialty : str | None = None       


class User_login(BaseModel):
    email : Annotated[str,EmailStr]
    password : str
    

class Update_password(BaseModel):
    last_password : str
    new_password : str = Field(min_length=6,max_length=15)