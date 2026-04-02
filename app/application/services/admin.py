from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.application.ports.repositories import AuthRepository, EmrRepository
from app.core.logging import get_logger
from app.core.metrics import observe_business_operation
from app.core.security import hash_password
from app.domain.entities import Doctor, Patient
from app.domain.enums import Gender, Role
from app.domain.exceptions import ConflictError


@dataclass(slots=True)
class CreateDoctorCommand:
    full_name: str
    specialization: str
    phone: str
    email: str
    username: str
    password: str


@dataclass(slots=True)
class CreatePatientCommand:
    full_name: str
    date_of_birth: date
    gender: Gender
    phone: str
    email: str
    address: str
    insurance_number: str
    username: str
    password: str


class AdminService:
    def __init__(self, auth_repository: AuthRepository, emr_repository: EmrRepository) -> None:
        self._auth_repository = auth_repository
        self._emr_repository = emr_repository
        self._logger = get_logger(__name__)

    async def create_doctor(self, command: CreateDoctorCommand) -> Doctor:
        with observe_business_operation("admin", "create_doctor", username=command.username):
            await self._ensure_unique_username(command.username)
            if await self._emr_repository.doctor_email_exists(command.email):
                raise ConflictError("Doctor with this email already exists.")

            user = await self._auth_repository.create_user(
                username=command.username,
                password_hash=hash_password(command.password),
                role=Role.DOCTOR,
            )
            doctor = await self._emr_repository.create_doctor(
                user_id=user.id,
                full_name=command.full_name,
                specialization=command.specialization,
                phone=command.phone,
                email=command.email,
            )
            self._logger.info(
                "doctor_created",
                extra={"doctor_id": doctor.id, "username": command.username},
            )
            return doctor

    async def create_patient(self, command: CreatePatientCommand) -> Patient:
        with observe_business_operation("admin", "create_patient", username=command.username):
            await self._ensure_unique_username(command.username)
            if await self._emr_repository.patient_email_exists(command.email):
                raise ConflictError("Patient with this email already exists.")
            if await self._emr_repository.insurance_number_exists(command.insurance_number):
                raise ConflictError("Patient with this insurance number already exists.")

            user = await self._auth_repository.create_user(
                username=command.username,
                password_hash=hash_password(command.password),
                role=Role.PATIENT,
            )
            patient = await self._emr_repository.create_patient(
                user_id=user.id,
                full_name=command.full_name,
                date_of_birth=command.date_of_birth,
                gender=command.gender,
                phone=command.phone,
                email=command.email,
                address=command.address,
                insurance_number=command.insurance_number,
            )
            self._logger.info(
                "patient_created",
                extra={"patient_id": patient.id, "username": command.username},
            )
            return patient

    async def _ensure_unique_username(self, username: str) -> None:
        if await self._auth_repository.username_exists(username):
            raise ConflictError("User with this username already exists.")
