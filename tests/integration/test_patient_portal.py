from httpx import AsyncClient

from tests.conftest import create_doctor, create_patient, login


async def test_patient_can_view_own_card(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    await create_doctor(client, admin_token, suffix="viewer")
    patient = await create_patient(client, admin_token, suffix="viewer")

    doctor_token = await login(client, "doctor_viewer", "DoctorPass123")
    patient_token = await login(client, "patient_viewer", "PatientPass123")

    await client.post(
        f"/api/v1/doctors/me/patients/{patient['id']}/assign",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    await client.post(
        f"/api/v1/doctors/me/patients/{patient['id']}/medical-records",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "visit_date": "2026-04-03T09:00:00Z",
            "complaints": "Fever",
            "diagnosis": "Cold",
            "examination_results": "Mild inflammation",
            "doctor_comment": "Monitor temperature",
        },
    )

    response = await client.get(
        "/api/v1/patients/me",
        headers={"Authorization": f"Bearer {patient_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["personal_data"]["id"] == patient["id"]
    assert payload["medical_records"][0]["diagnosis"] == "Cold"


async def test_patient_can_update_limited_personal_fields(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    await create_patient(client, admin_token, suffix="editable")
    patient_token = await login(client, "patient_editable", "PatientPass123")

    response = await client.patch(
        "/api/v1/patients/me",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={
            "phone": "+79991112233",
            "email": "updated.patient@example.com",
            "address": "Nevsky prospect 10",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["phone"] == "+79991112233"
    assert payload["email"] == "updated.patient@example.com"
    assert payload["address"] == "Nevsky prospect 10"


async def test_patient_cannot_use_doctor_endpoints(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    patient = await create_patient(client, admin_token, suffix="blocked")
    patient_token = await login(client, "patient_blocked", "PatientPass123")

    response = await client.get(
        f"/api/v1/doctors/me/patients/{patient['id']}",
        headers={"Authorization": f"Bearer {patient_token}"},
    )

    assert response.status_code == 403
