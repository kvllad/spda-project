from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.infrastructure.bootstrap import bootstrap_admin
from app.infrastructure.db.session import DatabaseManager
from app.main import create_app


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="test-emr-service",
        environment="test",
        debug=True,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        jwt_secret_key="test-secret-key",
        access_token_expire_minutes=60,
        admin_login="admin",
        admin_password="admin12345",
        admin_full_name="Test Admin",
    )


@pytest.fixture()
async def client(settings: Settings) -> AsyncIterator[AsyncClient]:
    database_manager = DatabaseManager(settings.database_url)
    await database_manager.create_all()
    await bootstrap_admin(database_manager.session_factory, settings)

    app = create_app(settings=settings, database_manager=database_manager)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as async_client:
        yield async_client

    await database_manager.dispose()


async def login(client: AsyncClient, username: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def create_doctor(client: AsyncClient, admin_token: str, suffix: str = "one") -> dict:
    response = await client.post(
        "/api/v1/admin/doctors",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": f"Dr. {suffix.title()}",
            "specialization": "Therapist",
            "phone": f"+7999000000{suffix[-1] if suffix[-1].isdigit() else '1'}",
            "email": f"doctor.{suffix}@example.com",
            "username": f"doctor_{suffix}",
            "password": "DoctorPass123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_patient(client: AsyncClient, admin_token: str, suffix: str = "one") -> dict:
    response = await client.post(
        "/api/v1/admin/patients",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": f"Patient {suffix.title()}",
            "date_of_birth": "1990-01-10",
            "gender": "female",
            "phone": f"+7888000000{suffix[-1] if suffix[-1].isdigit() else '1'}",
            "email": f"patient.{suffix}@example.com",
            "address": f"Lenina {suffix}",
            "insurance_number": f"POLICY-{suffix.upper()}",
            "username": f"patient_{suffix}",
            "password": "PatientPass123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
