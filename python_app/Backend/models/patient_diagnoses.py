from .Base import Base
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import ForeignKey
from typing import Annotated

primary = Annotated[int,mapped_column(primary_key=True)]


class Diagnoses(Base):
    __tablename__ = "diagnoses"
    id : Mapped[primary]
    patient_id : Mapped[int] = mapped_column(ForeignKey("patients.id",ondelete="CASCADE"), nullable=True)
    doctor_id : Mapped[int] = mapped_column(ForeignKey("doctors.id",ondelete="CASCADE"), nullable=True)
    request_id : Mapped[int] = mapped_column(ForeignKey("patients_requests.id",ondelete="CASCADE"), nullable=True)
    diagnoses : Mapped[str]
    description : Mapped[str]
    recommendations : Mapped[str]

    patients = relationship("Patients",back_populates="diagnoses")
    doctors = relationship("Doctors",back_populates="diagnoses") 
    patients_requests = relationship("Patients_Requests",back_populates="diagnoses")