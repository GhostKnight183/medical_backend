from sqlalchemy import ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship
from models.Base import Base
from typing import Annotated
import datetime

primary = Annotated[int,mapped_column(primary_key=True)]

class Messages(Base):
    __tablename__ = "messages"
    id : Mapped[primary]
    converstation_id : Mapped[int] 
    sender_id : Mapped[int]  
    recipient_id : Mapped[int]
    content : Mapped[str] = mapped_column(Text)
    created_at : Mapped[datetime.datetime] = mapped_column(default= datetime.datetime.utcnow()) 


class Converstations(Base):
    __tablename__ = "converstations"
    id : Mapped[primary]
    patient_id : Mapped[int] = mapped_column(ForeignKey("patients.id"))
    doctor_id : Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    started_at : Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow())

    patients = relationship("Patients",back_populates="converstations")
    doctors = relationship("Doctors",back_populates="converstations")