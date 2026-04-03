from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.services.doctor import (
    CreateMedicalRecordCommand,
    CreatePrescriptionCommand,
    DoctorService,
)
from app.application.services.patient import PatientService, UpdatePatientProfileCommand
from app.domain.entities import (
    Patient,
    PatientCard,
    PatientSummary,
    Prescription,
)
from app.domain.enums import Gender
from app.domain.exceptions import ConflictError, NotFoundError


def _now() -> datetime:
    return datetime(2026, 4, 3, 12, 0, tzinfo=UTC)


def _patient() -> Patient:
    return Patient(
        id="patient-1",
        user_id="user-1",
        full_name="Jane Doe",
        date_of_birth=date(1990, 1, 10),
        gender=Gender.FEMALE,
        phone="+78880000001",
        email="patient@example.com",
        address="Lenina 1",
        insurance_number="POLICY-001",
        created_at=_now(),
    )


def _patient_card() -> PatientCard:
    return PatientCard(
        personal_data=_patient(),
        assigned_doctor_id="doctor-1",
        medical_records=[],
        prescriptions=[],
        last_visit_at=None,
    )


@pytest.mark.asyncio
async def test_doctor_list_patients_returns_repository_data() -> None:
    repository = AsyncMock()
    repository.list_doctor_patients.return_value = [
        PatientSummary(
            id="patient-1",
            full_name="Jane Doe",
            date_of_birth=date(1990, 1, 10),
            insurance_number="POLICY-001",
            assigned_doctor_id="doctor-1",
            status="active",
            last_visit_at=None,
        )
    ]
    service = DoctorService(repository)

    patients = await service.list_patients("doctor-1")

    assert [patient.id for patient in patients] == ["patient-1"]


@pytest.mark.asyncio
async def test_assign_patient_translates_repository_conflict() -> None:
    repository = AsyncMock()
    repository.assign_patient.side_effect = ValueError("Patient already assigned.")
    service = DoctorService(repository)

    with pytest.raises(ConflictError, match="Patient already assigned"):
        await service.assign_patient("doctor-1", "patient-1")


@pytest.mark.asyncio
async def test_get_patient_card_raises_not_found_for_foreign_patient() -> None:
    repository = AsyncMock()
    repository.get_doctor_patient_card.return_value = None
    service = DoctorService(repository)

    with pytest.raises(NotFoundError, match="Patient card was not found"):
        await service.get_patient_card("doctor-2", "patient-1")


@pytest.mark.asyncio
async def test_add_medical_record_requires_access_to_patient_card() -> None:
    repository = AsyncMock()
    repository.get_doctor_patient_card.return_value = None
    service = DoctorService(repository)

    command = CreateMedicalRecordCommand(
        patient_id="patient-1",
        doctor_id="doctor-1",
        visit_date=_now(),
        complaints="Headache",
        diagnosis="Migraine",
        examination_results="Stable vitals",
        doctor_comment="Rest",
    )

    with pytest.raises(NotFoundError, match="Patient card was not found"):
        await service.add_medical_record(command)

    repository.add_medical_record.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_prescription_persists_prescription_for_assigned_patient() -> None:
    repository = AsyncMock()
    repository.get_doctor_patient_card.return_value = _patient_card()
    repository.add_prescription.return_value = Prescription(
        id="prescription-1",
        patient_id="patient-1",
        doctor_id="doctor-1",
        prescribed_at=_now(),
        title="Ibuprofen",
        dosage="200 mg",
        treatment_period="5 days",
        doctor_comment="After meals",
        created_at=_now(),
    )
    service = DoctorService(repository)

    command = CreatePrescriptionCommand(
        patient_id="patient-1",
        doctor_id="doctor-1",
        prescribed_at=_now(),
        title="Ibuprofen",
        dosage="200 mg",
        treatment_period="5 days",
        doctor_comment="After meals",
    )

    prescription = await service.add_prescription(command)

    assert prescription.id == "prescription-1"
    assert repository.add_prescription.await_args.kwargs["patient_id"] == "patient-1"


@pytest.mark.asyncio
async def test_patient_get_my_card_raises_not_found() -> None:
    repository = AsyncMock()
    repository.get_patient_card.return_value = None
    service = PatientService(repository)

    with pytest.raises(NotFoundError, match="Patient card was not found"):
        await service.get_my_card("patient-1")


@pytest.mark.asyncio
async def test_patient_update_profile_rejects_duplicate_email() -> None:
    repository = AsyncMock()
    repository.patient_email_exists.return_value = True
    service = PatientService(repository)

    command = UpdatePatientProfileCommand(
        patient_id="patient-1",
        email="taken@example.com",
    )

    with pytest.raises(ConflictError, match="email already exists"):
        await service.update_my_profile(command)

    repository.update_patient_contact_info.assert_not_awaited()


@pytest.mark.asyncio
async def test_patient_update_profile_returns_updated_patient() -> None:
    repository = AsyncMock()
    repository.patient_email_exists.return_value = False
    repository.update_patient_contact_info.return_value = _patient()
    service = PatientService(repository)

    command = UpdatePatientProfileCommand(
        patient_id="patient-1",
        phone="+79991112233",
        email="updated@example.com",
        address="Nevsky 10",
    )

    patient = await service.update_my_profile(command)

    assert patient.id == "patient-1"
    assert (
        repository.update_patient_contact_info.await_args.kwargs["email"]
        == "updated@example.com"
    )
