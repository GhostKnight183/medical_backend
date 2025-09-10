from sqlalchemy import ForeignKey,Enum as SQLEnum
from sqlalchemy.orm import Mapped,mapped_column,relationship
from enum import Enum
from typing import Annotated
from .Base import Base
import datetime

primary = Annotated[int,mapped_column(primary_key=True)]

class RequestStatus(str,Enum):
    pending = "pending"
    accepted = "accepted"


class Patients_Requests(Base):
    __tablename__ = "patients_requests"
    id : Mapped[primary]
    patient_id : Mapped[int] = mapped_column(ForeignKey("patients.id",ondelete="CASCADE"), nullable=True)
    doctor_id : Mapped[int] 
    requested_at : Mapped[datetime.datetime] = mapped_column(default= datetime.datetime.utcnow())
    status : Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus),default= RequestStatus.pending,nullable= False)
    confirmed_at : Mapped[datetime.datetime] = mapped_column(nullable= True)
    

    patients = relationship("Patients",back_populates="patients_requests")
    diagnoses = relationship("Diagnoses",back_populates="patients_requests")