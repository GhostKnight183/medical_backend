from pydantic import BaseModel


class Diagnose(BaseModel):
    diagnoses : str
    description : str
    recommendations : str


class Ban_user(BaseModel):
    reason : str
    ban_time : int
