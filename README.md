# EMR Service

Backend for an electronic medical record built with FastAPI, PostgreSQL, Alembic, Docker Compose, and Grafana/Loki/Prometheus.

## Quick Start

Run locally:

```bash
docker compose up -d --build
```

Main endpoints:

- API docs: `https://my-emr.duckdns.org/docs`
- ReDoc: `https://my-emr.duckdns.org/redoc`
- OpenAPI: `https://my-emr.duckdns.org/openapi.json`
- Health: `https://my-emr.duckdns.org/healthz`

For local development replace `my-emr.duckdns.org` with `127.0.0.1`.

## Authentication

Get an access token:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "YOUR_ADMIN_PASSWORD"
  }'
```

Response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "role": "admin",
  "profile_id": null
}
```

Use the token in all protected requests:

```bash
-H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Admin Flow

Create a doctor:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/admin/doctors \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "full_name": "Dr. Alice Smith",
    "specialization": "Therapist",
    "phone": "+79990000001",
    "email": "doctor.alice@example.com",
    "username": "doctor_alice",
    "password": "DoctorPass123"
  }'
```

Create a patient:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/admin/patients \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "full_name": "Ivan Petrov",
    "date_of_birth": "1990-01-10",
    "gender": "male",
    "phone": "+78880000001",
    "email": "ivan.petrov@example.com",
    "address": "Lenina 10",
    "insurance_number": "POLICY-001",
    "username": "patient_ivan",
    "password": "PatientPass123"
  }'
```

## Login as Created Users

Doctor login:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"doctor_alice","password":"DoctorPass123"}'
```

Patient login:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"patient_ivan","password":"PatientPass123"}'
```

The `profile_id` in the login response is the doctor or patient profile ID used by the application internally.

## Doctor Flow

List assigned patients:

```bash
curl https://my-emr.duckdns.org/api/v1/doctors/me/patients \
  -H "Authorization: Bearer <DOCTOR_TOKEN>"
```

List unassigned patients:

```bash
curl https://my-emr.duckdns.org/api/v1/doctors/me/patients/available \
  -H "Authorization: Bearer <DOCTOR_TOKEN>"
```

Assign a patient:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/doctors/me/patients/<PATIENT_ID>/assign \
  -H "Authorization: Bearer <DOCTOR_TOKEN>"
```

Add a medical record:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/doctors/me/patients/<PATIENT_ID>/medical-records \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <DOCTOR_TOKEN>" \
  -d '{
    "visit_date": "2026-04-03T10:00:00Z",
    "complaints": "Headache",
    "diagnosis": "Migraine",
    "examination_results": "Stable vitals",
    "doctor_comment": "Hydration and rest"
  }'
```

Add a prescription:

```bash
curl -X POST https://my-emr.duckdns.org/api/v1/doctors/me/patients/<PATIENT_ID>/prescriptions \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <DOCTOR_TOKEN>" \
  -d '{
    "prescribed_at": "2026-04-03T10:30:00Z",
    "title": "Ibuprofen",
    "dosage": "200 mg",
    "treatment_period": "5 days",
    "doctor_comment": "After meals"
  }'
```

## Patient Flow

View own medical card:

```bash
curl https://my-emr.duckdns.org/api/v1/patients/me \
  -H "Authorization: Bearer <PATIENT_TOKEN>"
```

Update contact information:

```bash
curl -X PATCH https://my-emr.duckdns.org/api/v1/patients/me \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer <PATIENT_TOKEN>" \
  -d '{
    "phone": "+79991112233",
    "email": "updated.patient@example.com",
    "address": "Nevsky prospect 10"
  }'
```

## Observability

- Grafana: `https://my-emr.duckdns.org/grafana/`
- Prometheus: `http://213.171.29.112:9090`
- Loki: `http://213.171.29.112:3100`

## TLS and DuckDNS

Production traffic is served through `nginx` with Let's Encrypt certificates for `my-emr.duckdns.org`. Renewal is handled on the VPS by `scripts/renew_tls.sh`, which uses the DuckDNS TXT API hooks in `ops/certbot/` for DNS-01 validation. Runtime certificate files live outside git in `ops/letsencrypt/`.

## Validation

Useful local checks:

```bash
./.venv/bin/ruff check .
./.venv/bin/pytest -q
```
