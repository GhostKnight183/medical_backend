from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import ForeignKey,Index,Enum as SQLEnum
from enum import Enum
from typing import Annotated
from models.Base import Base
import datetime


primary = Annotated[int,mapped_column(primary_key=True)]


class UsersRole(str,Enum):
    Patients = "Patient"
    Doctors = "Doctor"
    Admins = "Admin"


class SpecialtyEnum(str, Enum):
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    PEDIATRICS = "pediatrics"
    DERMATOLOGY = "dermatology"
    SURGERY = "surgery"
    ONCOLOGY = "oncology"
    DIAGNOSTICS = "diagnostics"
    PSYCHIATRY = "psychiatry"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    UROLOGY = "urology"
    ORTHOPEDICS = "orthopedics"
    OPHTHALMOLOGY = "ophthalmology"
    ANESTHESIOLOGY = "anesthesiology"
    GASTROENTEROLOGY = "gastroenterology"
    ENDOCRINOLOGY = "endocrinology"
    PULMONOLOGY = "pulmonology"
    INFECTIOUS_DISEASE = "infectious_disease"
    RHEUMATOLOGY = "rheumatology"
    NEPHROLOGY = "nephrology"
    HEMATOLOGY = "hematology"
    IMMUNOLOGY = "immunology"
    OBSTETRICS_GYNECOLOGY = "obstetrics_gynecology"
    EMERGENCY_MEDICINE = "emergency_medicine"
    CRITICAL_CARE = "critical_care"
    PHYSICAL_MEDICINE = "physical_medicine"
    PREVENTIVE_MEDICINE = "preventive_medicine"
    FAMILY_MEDICINE = "family_medicine"
    GENERAL_PRACTICE = "general_practice"
    TRAUMA_SURGERY = "trauma_surgery"
    VASCULAR_SURGERY = "vascular_surgery"
    PLASTIC_SURGERY = "plastic_surgery"
    THORACIC_SURGERY = "thoracic_surgery"
    TRANSPLANT_SURGERY = "transplant_surgery"
    FORENSIC_PATHOLOGY = "forensic_pathology"
    SLEEP_MEDICINE = "sleep_medicine"
    SPORTS_MEDICINE = "sports_medicine"
    GERIATRICS = "geriatrics"
    NEONATOLOGY = "neonatology"
    REPRODUCTIVE_MEDICINE = "reproductive_medicine"
    ALLERGY_IMMUNOLOGY = "allergy_immunology"
    OCCUPATIONAL_MEDICINE = "occupational_medicine"
    HOSPICE_PALLIATIVE = "hospice_palliative"
    UNDERSEA_MEDICINE = "undersea_medicine"
    AEROSPACE_MEDICINE = "aerospace_medicine"


class UsersAuth(Base):
    __tablename__ = "usersauth"
    id : Mapped[primary]
    FullName : Mapped[str]
    email : Mapped[str] = mapped_column(unique= True)
    password : Mapped[bytes]
    role : Mapped[UsersRole] = mapped_column(SQLEnum(UsersRole),default = UsersRole.Patients)
    is_verified : Mapped[bool] = mapped_column(default=False)
    is_banned : Mapped[bool] = mapped_column(default=False)

    __table_args__ = (
        Index("email_index","email"),
    )

class Patients(Base):
    __tablename__ = "patients"
    id : Mapped[primary]
    FullName : Mapped[str]
    email : Mapped[str] = mapped_column(unique= True)
    Location_id : Mapped[int] = mapped_column(ForeignKey("locations.id",ondelete="CASCADE"), nullable=True)
    created_at : Mapped[datetime.datetime] = mapped_column(default= datetime.datetime.utcnow())
    role : Mapped[UsersRole] = mapped_column(SQLEnum(UsersRole),default=UsersRole.Patients)
    doctor_id : Mapped[int] = mapped_column(ForeignKey("doctors.id",ondelete="CASCADE"), nullable=True)

    __table_args__ = (
        Index("email_doctor_index","email","doctor_id"),
    )

    doctors = relationship("Doctors",back_populates="patients")
    locations = relationship("Locations",back_populates="patients")
    patients_requests = relationship("Patients_Requests",back_populates="patients")
    diagnoses = relationship("Diagnoses",back_populates="patients")
    converstations = relationship("Converstations",back_populates="patients")
    grades = relationship("Grades",back_populates = "patients")


class Doctors(Base):
    __tablename__ = "doctors"
    id : Mapped[primary]
    FullName : Mapped[str]
    email : Mapped[str]
    Location_id : Mapped[int] = mapped_column(ForeignKey("locations.id",ondelete="CASCADE"), nullable=True)
    created_at : Mapped[datetime.datetime] = mapped_column(default= datetime.datetime.utcnow())
    role : Mapped[UsersRole] = mapped_column(SQLEnum(UsersRole),default= UsersRole.Doctors)
    specialty : Mapped[SpecialtyEnum] = mapped_column(SQLEnum(SpecialtyEnum))
    total_visits : Mapped[int] = mapped_column(nullable=True)

    __table_args__ = (
        Index("email_specialty_index","email","specialty"),
    )

    patients = relationship("Patients",back_populates="doctors")
    locations = relationship("Locations",back_populates="doctors")
    diagnoses = relationship("Diagnoses",back_populates="doctors")
    converstations = relationship("Converstations",back_populates="doctors")
    grades = relationship("Grades",back_populates = "doctors")

class Admins(Base):
    __tablename__ = "admins"
    id: Mapped[primary]
    FullName : Mapped[str]
    email : Mapped[str]
    Location_id : Mapped[int] = mapped_column(ForeignKey("locations.id",ondelete="CASCADE"))
    created_at : Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow())
    role : Mapped[UsersRole] = mapped_column(SQLEnum(UsersRole),default= UsersRole.Admins)

    __table_args__ = (
        Index("email_index","email"),
    )

    locations = relationship("Locations",back_populates="admins")
    banned_users = relationship("Banned_users",back_populates="admins")


class Locations(Base):
    __tablename__ = "locations"
    id: Mapped[primary]
    Country: Mapped[str]
    City: Mapped[str]
    Region: Mapped[str]            
    AddressLine: Mapped[str]  

    doctors = relationship("Doctors",back_populates="locations")
    patients = relationship("Patients",back_populates="locations")
    admins = relationship("Admins",back_populates="locations")

class Grades(Base):
    __tablename__ = "grades"
    id : Mapped[primary]
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id",ondelete = "CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id",ondelete = "CASCADE"))
    stars: Mapped[float]
    created_at: Mapped[datetime.datetime] = mapped_column(default = datetime.datetime.utcnow())

    __table_args__ = (
        Index("doctor_index","doctor_id"),
    )

    patients = relationship("Patients",back_populates="grades")
    doctors = relationship("Doctors",back_populates="grades")