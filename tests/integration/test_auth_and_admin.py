from httpx import AsyncClient

from tests.conftest import create_doctor, login


async def test_admin_can_create_doctor_and_doctor_can_login(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    doctor = await create_doctor(client, admin_token, suffix="auth")

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "doctor_auth", "password": "DoctorPass123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["role"] == "doctor"
    assert payload["profile_id"] == doctor["id"]


async def test_admin_endpoints_require_admin_role(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    await create_doctor(client, admin_token, suffix="guard")
    doctor_token = await login(client, "doctor_guard", "DoctorPass123")

    response = await client.post(
        "/api/v1/admin/doctors",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "full_name": "Blocked Doctor",
            "specialization": "Therapist",
            "phone": "+79990000099",
            "email": "blocked@example.com",
            "username": "blocked_doctor",
            "password": "DoctorPass123",
        },
    )

    assert response.status_code == 403
