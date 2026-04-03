from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.services.admin import (
    AdminService,
    CreateDoctorCommand,
    CreatePatientCommand,
)
from app.core.security import verify_password
from app.domain.entities import Doctor, Patient, UserAccount
from app.domain.enums import Gender, Role
from app.domain.exceptions import ConflictError


def _now() -> datetime:
    return datetime(2026, 4, 3, 12, 0, tzinfo=UTC)


def _user_account() -> UserAccount:
    return UserAccount(
        id="user-1",
        username="doctor_user",
        password_hash="hashed",
        role=Role.DOCTOR,
        is_active=True,
        created_at=_now(),
    )


def _doctor() -> Doctor:
    return Doctor(
        id="doctor-1",
        user_id="user-1",
        full_name="Dr. House",
        specialization="Therapist",
        phone="+79990000001",
        email="doctor@example.com",
        created_at=_now(),
    )


def _patient() -> Patient:
    return Patient(
        id="patient-1",
        user_id="user-2",
        full_name="Jane Doe",
        date_of_birth=date(1990, 1, 10),
        gender=Gender.FEMALE,
        phone="+78880000001",
        email="patient@example.com",
        address="Lenina 1",
        insurance_number="POLICY-001",
        created_at=_now(),
    )


@pytest.mark.asyncio
async def test_create_doctor_creates_user_and_doctor_with_hashed_password() -> None:
    auth_repository = AsyncMock()
    emr_repository = AsyncMock()
    auth_repository.username_exists.return_value = False
    emr_repository.doctor_email_exists.return_value = False
    auth_repository.create_user.return_value = _user_account()
    emr_repository.create_doctor.return_value = _doctor()
    service = AdminService(auth_repository, emr_repository)

    command = CreateDoctorCommand(
        full_name="Dr. House",
        specialization="Therapist",
        phone="+79990000001",
        email="doctor@example.com",
        username="doctor_user",
        password="DoctorPass123",
    )

    doctor = await service.create_doctor(command)

    assert doctor.id == "doctor-1"
    assert auth_repository.create_user.await_args.kwargs["username"] == "doctor_user"
    assert auth_repository.create_user.await_args.kwargs["role"] is Role.DOCTOR
    assert verify_password(
        "DoctorPass123",
        auth_repository.create_user.await_args.kwargs["password_hash"],
    )
    assert emr_repository.create_doctor.await_args.kwargs["user_id"] == "user-1"


@pytest.mark.asyncio
async def test_create_doctor_raises_conflict_for_existing_username() -> None:
    auth_repository = AsyncMock()
    emr_repository = AsyncMock()
    auth_repository.username_exists.return_value = True
    service = AdminService(auth_repository, emr_repository)

    command = CreateDoctorCommand(
        full_name="Dr. House",
        specialization="Therapist",
        phone="+79990000001",
        email="doctor@example.com",
        username="doctor_user",
        password="DoctorPass123",
    )

    with pytest.raises(ConflictError, match="username already exists"):
        await service.create_doctor(command)

    emr_repository.doctor_email_exists.assert_not_awaited()
    auth_repository.create_user.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_patient_raises_conflict_for_duplicate_insurance_number() -> None:
    auth_repository = AsyncMock()
    emr_repository = AsyncMock()
    auth_repository.username_exists.return_value = False
    emr_repository.patient_email_exists.return_value = False
    emr_repository.insurance_number_exists.return_value = True
    service = AdminService(auth_repository, emr_repository)

    command = CreatePatientCommand(
        full_name="Jane Doe",
        date_of_birth=date(1990, 1, 10),
        gender=Gender.FEMALE,
        phone="+78880000001",
        email="patient@example.com",
        address="Lenina 1",
        insurance_number="POLICY-001",
        username="patient_user",
        password="PatientPass123",
    )

    with pytest.raises(ConflictError, match="insurance number already exists"):
        await service.create_patient(command)

    auth_repository.create_user.assert_not_awaited()
    emr_repository.create_patient.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_patient_creates_domain_objects() -> None:
    auth_repository = AsyncMock()
    emr_repository = AsyncMock()
    auth_repository.username_exists.return_value = False
    emr_repository.patient_email_exists.return_value = False
    emr_repository.insurance_number_exists.return_value = False
    auth_repository.create_user.return_value = UserAccount(
        id="user-2",
        username="patient_user",
        password_hash="hashed",
        role=Role.PATIENT,
        is_active=True,
        created_at=_now(),
    )
    emr_repository.create_patient.return_value = _patient()
    service = AdminService(auth_repository, emr_repository)

    command = CreatePatientCommand(
        full_name="Jane Doe",
        date_of_birth=date(1990, 1, 10),
        gender=Gender.FEMALE,
        phone="+78880000001",
        email="patient@example.com",
        address="Lenina 1",
        insurance_number="POLICY-001",
        username="patient_user",
        password="PatientPass123",
    )

    patient = await service.create_patient(command)

    assert patient.id == "patient-1"
    assert auth_repository.create_user.await_args.kwargs["role"] is Role.PATIENT
    assert verify_password(
        "PatientPass123",
        auth_repository.create_user.await_args.kwargs["password_hash"],
    )
    assert emr_repository.create_patient.await_args.kwargs["insurance_number"] == "POLICY-001"
