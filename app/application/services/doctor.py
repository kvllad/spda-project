from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.application.ports.repositories import EmrRepository
from app.core.logging import get_logger
from app.core.metrics import observe_business_operation
from app.domain.entities import DoctorPatientAssignment, MedicalRecord, PatientCard, PatientSummary, Prescription
from app.domain.exceptions import ConflictError, NotFoundError


@dataclass(slots=True)
class CreateMedicalRecordCommand:
    patient_id: str
    doctor_id: str
    visit_date: datetime
    complaints: str
    diagnosis: str
    examination_results: str
    doctor_comment: str


@dataclass(slots=True)
class CreatePrescriptionCommand:
    patient_id: str
    doctor_id: str
    prescribed_at: datetime
    title: str
    dosage: str
    treatment_period: str
    doctor_comment: str


class DoctorService:
    def __init__(self, emr_repository: EmrRepository) -> None:
        self._emr_repository = emr_repository
        self._logger = get_logger(__name__)

    async def list_patients(self, doctor_id: str) -> list[PatientSummary]:
        with observe_business_operation("doctor", "list_patients", doctor_id=doctor_id):
            return await self._emr_repository.list_doctor_patients(doctor_id)

    async def list_available_patients(self) -> list[PatientSummary]:
        with observe_business_operation("doctor", "list_available_patients"):
            return await self._emr_repository.list_unassigned_patients()

    async def assign_patient(self, doctor_id: str, patient_id: str) -> DoctorPatientAssignment:
        with observe_business_operation(
            "doctor",
            "assign_patient",
            doctor_id=doctor_id,
            patient_id=patient_id,
        ):
            try:
                assignment = await self._emr_repository.assign_patient(doctor_id, patient_id)
            except ValueError as error:
                raise ConflictError(str(error)) from error
            self._logger.info(
                "patient_assigned",
                extra={"doctor_id": doctor_id, "patient_id": patient_id},
            )
            return assignment

    async def get_patient_card(self, doctor_id: str, patient_id: str) -> PatientCard:
        with observe_business_operation(
            "doctor",
            "get_patient_card",
            doctor_id=doctor_id,
            patient_id=patient_id,
        ):
            card = await self._emr_repository.get_doctor_patient_card(doctor_id, patient_id)
            if card is None:
                raise NotFoundError("Patient card was not found for this doctor.")
            return card

    async def add_medical_record(self, command: CreateMedicalRecordCommand) -> MedicalRecord:
        with observe_business_operation(
            "doctor",
            "add_medical_record",
            doctor_id=command.doctor_id,
            patient_id=command.patient_id,
        ):
            await self.get_patient_card(command.doctor_id, command.patient_id)
            record = await self._emr_repository.add_medical_record(
                patient_id=command.patient_id,
                doctor_id=command.doctor_id,
                visit_date=command.visit_date,
                complaints=command.complaints,
                diagnosis=command.diagnosis,
                examination_results=command.examination_results,
                doctor_comment=command.doctor_comment,
            )
            self._logger.info(
                "medical_record_created",
                extra={"doctor_id": command.doctor_id, "patient_id": command.patient_id},
            )
            return record

    async def add_prescription(self, command: CreatePrescriptionCommand) -> Prescription:
        with observe_business_operation(
            "doctor",
            "add_prescription",
            doctor_id=command.doctor_id,
            patient_id=command.patient_id,
        ):
            await self.get_patient_card(command.doctor_id, command.patient_id)
            prescription = await self._emr_repository.add_prescription(
                patient_id=command.patient_id,
                doctor_id=command.doctor_id,
                prescribed_at=command.prescribed_at,
                title=command.title,
                dosage=command.dosage,
                treatment_period=command.treatment_period,
                doctor_comment=command.doctor_comment,
            )
            self._logger.info(
                "prescription_created",
                extra={"doctor_id": command.doctor_id, "patient_id": command.patient_id},
            )
            return prescription
