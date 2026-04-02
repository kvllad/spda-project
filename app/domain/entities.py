from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.enums import Gender, Role


@dataclass(slots=True)
class UserAccount:
    id: str
    username: str
    password_hash: str
    role: Role
    is_active: bool
    created_at: datetime


@dataclass(slots=True)
class Doctor:
    id: str
    user_id: str
    full_name: str
    specialization: str
    phone: str
    email: str
    created_at: datetime


@dataclass(slots=True)
class Patient:
    id: str
    user_id: str
    full_name: str
    date_of_birth: date
    gender: Gender
    phone: str
    email: str
    address: str
    insurance_number: str
    created_at: datetime


@dataclass(slots=True)
class DoctorPatientAssignment:
    id: str
    doctor_id: str
    patient_id: str
    assigned_at: datetime


@dataclass(slots=True)
class MedicalRecord:
    id: str
    patient_id: str
    doctor_id: str
    visit_date: datetime
    complaints: str
    diagnosis: str
    examination_results: str
    doctor_comment: str
    created_at: datetime


@dataclass(slots=True)
class Prescription:
    id: str
    patient_id: str
    doctor_id: str
    prescribed_at: datetime
    title: str
    dosage: str
    treatment_period: str
    doctor_comment: str
    created_at: datetime


@dataclass(slots=True)
class PatientSummary:
    id: str
    full_name: str
    date_of_birth: date
    insurance_number: str
    assigned_doctor_id: str | None
    status: str
    last_visit_at: datetime | None


@dataclass(slots=True)
class PatientCard:
    personal_data: Patient
    assigned_doctor_id: str | None
    medical_records: list[MedicalRecord] = field(default_factory=list)
    prescriptions: list[Prescription] = field(default_factory=list)
    last_visit_at: datetime | None = None


@dataclass(slots=True)
class AuthContext:
    user_id: str
    role: Role
    profile_id: str | None
