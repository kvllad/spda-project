from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from app.domain.entities import (
    Doctor,
    DoctorPatientAssignment,
    MedicalRecord,
    Patient,
    PatientCard,
    PatientSummary,
    Prescription,
    UserAccount,
)
from app.domain.enums import Gender, Role


class AuthRepository(Protocol):
    async def get_user_by_username(self, username: str) -> UserAccount | None: ...

    async def get_doctor_by_user_id(self, user_id: str) -> Doctor | None: ...

    async def get_patient_by_user_id(self, user_id: str) -> Patient | None: ...

    async def username_exists(self, username: str) -> bool: ...

    async def create_user(self, *, username: str, password_hash: str, role: Role) -> UserAccount: ...


class EmrRepository(Protocol):
    async def doctor_email_exists(self, email: str) -> bool: ...

    async def patient_email_exists(self, email: str, exclude_patient_id: str | None = None) -> bool: ...

    async def insurance_number_exists(self, insurance_number: str) -> bool: ...

    async def create_doctor(
        self,
        *,
        user_id: str,
        full_name: str,
        specialization: str,
        phone: str,
        email: str,
    ) -> Doctor: ...

    async def create_patient(
        self,
        *,
        user_id: str,
        full_name: str,
        date_of_birth: date,
        gender: Gender,
        phone: str,
        email: str,
        address: str,
        insurance_number: str,
    ) -> Patient: ...

    async def list_doctor_patients(self, doctor_id: str) -> list[PatientSummary]: ...

    async def list_unassigned_patients(self) -> list[PatientSummary]: ...

    async def assign_patient(self, doctor_id: str, patient_id: str) -> DoctorPatientAssignment: ...

    async def get_doctor_patient_card(self, doctor_id: str, patient_id: str) -> PatientCard | None: ...

    async def get_patient_card(self, patient_id: str) -> PatientCard | None: ...

    async def add_medical_record(
        self,
        *,
        patient_id: str,
        doctor_id: str,
        visit_date: datetime,
        complaints: str,
        diagnosis: str,
        examination_results: str,
        doctor_comment: str,
    ) -> MedicalRecord: ...

    async def add_prescription(
        self,
        *,
        patient_id: str,
        doctor_id: str,
        prescribed_at: datetime,
        title: str,
        dosage: str,
        treatment_period: str,
        doctor_comment: str,
    ) -> Prescription: ...

    async def update_patient_contact_info(
        self,
        *,
        patient_id: str,
        phone: str | None,
        email: str | None,
        address: str | None,
    ) -> Patient | None: ...
