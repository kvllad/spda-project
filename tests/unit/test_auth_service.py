from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.services.auth import AuthService
from app.core.config import Settings
from app.core.security import decode_access_token, hash_password
from app.domain.entities import Doctor, Patient, UserAccount
from app.domain.enums import Gender, Role
from app.domain.exceptions import AuthenticationError


def _settings() -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///unit.db",
        jwt_secret_key="0123456789abcdef0123456789abcdef",
        log_file_path="logs/unit-auth.log",
    )


def _now() -> datetime:
    return datetime(2026, 4, 3, 12, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_login_returns_token_for_doctor_and_resolves_profile() -> None:
    repository = AsyncMock()
    repository.get_user_by_username.return_value = UserAccount(
        id="user-1",
        username="doctor_user",
        password_hash=hash_password("DoctorPass123"),
        role=Role.DOCTOR,
        is_active=True,
        created_at=_now(),
    )
    repository.get_doctor_by_user_id.return_value = Doctor(
        id="doctor-1",
        user_id="user-1",
        full_name="Dr. House",
        specialization="Therapist",
        phone="+79990000001",
        email="doctor@example.com",
        created_at=_now(),
    )
    service = AuthService(repository, _settings())

    result = await service.login("doctor_user", "DoctorPass123")

    payload = decode_access_token(result.access_token, _settings())
    assert result.token_type == "bearer"
    assert result.role is Role.DOCTOR
    assert result.profile_id == "doctor-1"
    assert payload["sub"] == "user-1"
    assert payload["role"] == "doctor"
    assert payload["profile_id"] == "doctor-1"


@pytest.mark.asyncio
async def test_login_returns_patient_profile_id() -> None:
    repository = AsyncMock()
    repository.get_user_by_username.return_value = UserAccount(
        id="user-2",
        username="patient_user",
        password_hash=hash_password("PatientPass123"),
        role=Role.PATIENT,
        is_active=True,
        created_at=_now(),
    )
    repository.get_patient_by_user_id.return_value = Patient(
        id="patient-1",
        user_id="user-2",
        full_name="Jane Doe",
        date_of_birth=datetime(1990, 1, 10, tzinfo=UTC).date(),
        gender=Gender.FEMALE,
        phone="+78880000001",
        email="patient@example.com",
        address="Lenina 1",
        insurance_number="POLICY-001",
        created_at=_now(),
    )
    service = AuthService(repository, _settings())

    result = await service.login("patient_user", "PatientPass123")

    assert result.role is Role.PATIENT
    assert result.profile_id == "patient-1"


@pytest.mark.asyncio
async def test_login_rejects_inactive_user() -> None:
    repository = AsyncMock()
    repository.get_user_by_username.return_value = UserAccount(
        id="user-1",
        username="doctor_user",
        password_hash=hash_password("DoctorPass123"),
        role=Role.DOCTOR,
        is_active=False,
        created_at=_now(),
    )
    service = AuthService(repository, _settings())

    with pytest.raises(AuthenticationError, match="Invalid username or password"):
        await service.login("doctor_user", "DoctorPass123")

    repository.get_doctor_by_user_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_rejects_invalid_password() -> None:
    repository = AsyncMock()
    repository.get_user_by_username.return_value = UserAccount(
        id="user-1",
        username="doctor_user",
        password_hash=hash_password("DoctorPass123"),
        role=Role.DOCTOR,
        is_active=True,
        created_at=_now(),
    )
    service = AuthService(repository, _settings())

    with pytest.raises(AuthenticationError, match="Invalid username or password"):
        await service.login("doctor_user", "WrongPass123")


@pytest.mark.asyncio
async def test_login_returns_admin_without_profile() -> None:
    repository = AsyncMock()
    repository.get_user_by_username.return_value = UserAccount(
        id="admin-1",
        username="admin",
        password_hash=hash_password("AdminPass123"),
        role=Role.ADMIN,
        is_active=True,
        created_at=_now(),
    )
    service = AuthService(repository, _settings())

    result = await service.login("admin", "AdminPass123")

    assert result.role is Role.ADMIN
    assert result.profile_id is None
    repository.get_doctor_by_user_id.assert_not_awaited()
    repository.get_patient_by_user_id.assert_not_awaited()
