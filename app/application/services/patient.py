from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.repositories import EmrRepository
from app.core.logging import get_logger
from app.core.metrics import observe_business_operation
from app.domain.entities import Patient, PatientCard
from app.domain.exceptions import ConflictError, NotFoundError


@dataclass(slots=True)
class UpdatePatientProfileCommand:
    patient_id: str
    phone: str | None = None
    email: str | None = None
    address: str | None = None


class PatientService:
    def __init__(self, emr_repository: EmrRepository) -> None:
        self._emr_repository = emr_repository
        self._logger = get_logger(__name__)

    async def get_my_card(self, patient_id: str) -> PatientCard:
        with observe_business_operation("patient", "get_my_card", patient_id=patient_id):
            card = await self._emr_repository.get_patient_card(patient_id)
            if card is None:
                raise NotFoundError("Patient card was not found.")
            return card

    async def update_my_profile(self, command: UpdatePatientProfileCommand) -> Patient:
        with observe_business_operation("patient", "update_my_profile", patient_id=command.patient_id):
            if command.email and await self._emr_repository.patient_email_exists(
                command.email,
                exclude_patient_id=command.patient_id,
            ):
                raise ConflictError("Patient with this email already exists.")

            patient = await self._emr_repository.update_patient_contact_info(
                patient_id=command.patient_id,
                phone=command.phone,
                email=command.email,
                address=command.address,
            )
            if patient is None:
                raise NotFoundError("Patient profile was not found.")
            self._logger.info("patient_profile_updated", extra={"patient_id": command.patient_id})
            return patient
