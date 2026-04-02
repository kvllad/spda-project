from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import Gender, Role


class TokenRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: Role
    profile_id: str | None


class DoctorCreateRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    specialization: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=5, max_length=32)
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class PatientCreateRequest(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    date_of_birth: date
    gender: Gender
    phone: str = Field(min_length=5, max_length=32)
    email: EmailStr
    address: str = Field(min_length=5, max_length=255)
    insurance_number: str = Field(min_length=3, max_length=64)
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: str
    specialization: str
    phone: str
    email: EmailStr
    created_at: datetime


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    full_name: str
    date_of_birth: date
    gender: Gender
    phone: str
    email: EmailStr
    address: str
    insurance_number: str
    created_at: datetime


class PatientSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    date_of_birth: date
    insurance_number: str
    assigned_doctor_id: str | None
    status: str
    last_visit_at: datetime | None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doctor_id: str
    patient_id: str
    assigned_at: datetime


class MedicalRecordCreateRequest(BaseModel):
    visit_date: datetime
    complaints: str = Field(min_length=2)
    diagnosis: str = Field(min_length=2)
    examination_results: str = Field(min_length=2)
    doctor_comment: str = Field(min_length=2)


class PrescriptionCreateRequest(BaseModel):
    prescribed_at: datetime
    title: str = Field(min_length=2, max_length=255)
    dosage: str = Field(min_length=2, max_length=255)
    treatment_period: str = Field(min_length=2, max_length=255)
    doctor_comment: str = Field(min_length=2)


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    visit_date: datetime
    complaints: str
    diagnosis: str
    examination_results: str
    doctor_comment: str
    created_at: datetime


class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    doctor_id: str
    prescribed_at: datetime
    title: str
    dosage: str
    treatment_period: str
    doctor_comment: str
    created_at: datetime


class PatientCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    personal_data: PatientResponse
    assigned_doctor_id: str | None
    medical_records: list[MedicalRecordResponse]
    prescriptions: list[PrescriptionResponse]
    last_visit_at: datetime | None


class PatientUpdateRequest(BaseModel):
    phone: str | None = Field(default=None, min_length=5, max_length=32)
    email: EmailStr | None = None
    address: str | None = Field(default=None, min_length=5, max_length=255)
