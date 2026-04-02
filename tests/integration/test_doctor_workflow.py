from httpx import AsyncClient

from tests.conftest import create_doctor, create_patient, login


async def test_doctor_sees_only_assigned_patients(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    doctor = await create_doctor(client, admin_token, suffix="alpha")
    other_doctor = await create_doctor(client, admin_token, suffix="beta")
    patient_one = await create_patient(client, admin_token, suffix="first")
    patient_two = await create_patient(client, admin_token, suffix="second")

    doctor_token = await login(client, "doctor_alpha", "DoctorPass123")
    other_doctor_token = await login(client, "doctor_beta", "DoctorPass123")

    assign_first = await client.post(
        f"/api/v1/doctors/me/patients/{patient_one['id']}/assign",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assign_second = await client.post(
        f"/api/v1/doctors/me/patients/{patient_two['id']}/assign",
        headers={"Authorization": f"Bearer {other_doctor_token}"},
    )

    assert assign_first.status_code == 201
    assert assign_second.status_code == 201

    response = await client.get(
        "/api/v1/doctors/me/patients",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload] == [patient_one["id"]]
    assert payload[0]["assigned_doctor_id"] == doctor["id"]
    assert payload[0]["last_visit_at"] is None
    assert other_doctor["id"] != doctor["id"]


async def test_doctor_can_assign_from_pool_and_add_clinical_data(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    await create_doctor(client, admin_token, suffix="care")
    patient = await create_patient(client, admin_token, suffix="care")
    doctor_token = await login(client, "doctor_care", "DoctorPass123")

    available_before = await client.get(
        "/api/v1/doctors/me/patients/available",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert available_before.status_code == 200
    assert [item["id"] for item in available_before.json()] == [patient["id"]]

    assign_response = await client.post(
        f"/api/v1/doctors/me/patients/{patient['id']}/assign",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert assign_response.status_code == 201

    record_response = await client.post(
        f"/api/v1/doctors/me/patients/{patient['id']}/medical-records",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "visit_date": "2026-04-02T10:30:00Z",
            "complaints": "Headache",
            "diagnosis": "Migraine",
            "examination_results": "Stable vitals",
            "doctor_comment": "Need hydration and rest",
        },
    )
    prescription_response = await client.post(
        f"/api/v1/doctors/me/patients/{patient['id']}/prescriptions",
        headers={"Authorization": f"Bearer {doctor_token}"},
        json={
            "prescribed_at": "2026-04-02T11:00:00Z",
            "title": "Ibuprofen",
            "dosage": "200 mg",
            "treatment_period": "5 days",
            "doctor_comment": "After meals",
        },
    )

    assert record_response.status_code == 201
    assert prescription_response.status_code == 201

    card_response = await client.get(
        f"/api/v1/doctors/me/patients/{patient['id']}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )

    assert card_response.status_code == 200
    card = card_response.json()
    assert card["personal_data"]["id"] == patient["id"]
    assert card["last_visit_at"] == "2026-04-02T10:30:00Z"
    assert card["medical_records"][0]["diagnosis"] == "Migraine"
    assert card["prescriptions"][0]["title"] == "Ibuprofen"


async def test_doctor_cannot_open_foreign_patient_card(client: AsyncClient) -> None:
    admin_token = await login(client, "admin", "admin12345")
    await create_doctor(client, admin_token, suffix="owner")
    await create_doctor(client, admin_token, suffix="outsider")
    patient = await create_patient(client, admin_token, suffix="isolated")

    owner_token = await login(client, "doctor_owner", "DoctorPass123")
    outsider_token = await login(client, "doctor_outsider", "DoctorPass123")

    assign_response = await client.post(
        f"/api/v1/doctors/me/patients/{patient['id']}/assign",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert assign_response.status_code == 201

    response = await client.get(
        f"/api/v1/doctors/me/patients/{patient['id']}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )

    assert response.status_code == 404
