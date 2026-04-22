#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:?BASE_URL is required}"
ADMIN_LOGIN="${ADMIN_LOGIN:?ADMIN_LOGIN is required}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "${WORKDIR}"' EXIT

suffix="$(date +%s)"

request() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local token="${4:-}"
  local outfile="$5"

  local args=(-sS -X "$method" "${BASE_URL}${path}" -o "$outfile" -w "%{http_code}")
  if [[ -n "$token" ]]; then
    args+=(-H "Authorization: Bearer ${token}")
  fi
  if [[ -n "$body" ]]; then
    args+=(-H "Content-Type: application/json" -d "$body")
  fi
  curl "${args[@]}"
}

json_field() {
  local file="$1"
  local expr="$2"
  python3 - "$file" "$expr" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1], "r", encoding="utf-8"))
value = data
for part in sys.argv[2].split("."):
    if part.isdigit():
        value = value[int(part)]
    else:
        value = value[part]
if isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(value)
PY
}

assert_status() {
  local actual="$1"
  local expected="$2"
  local file="$3"
  if [[ "$actual" != "$expected" ]]; then
    echo "Unexpected status: got ${actual}, expected ${expected}" >&2
    cat "$file" >&2
    exit 1
  fi
}

health_body="${WORKDIR}/health.json"
health_status="$(request GET /healthz "" "" "${health_body}")"
assert_status "${health_status}" "200" "${health_body}"

docs_body="${WORKDIR}/docs.html"
docs_status="$(request GET /docs "" "" "${docs_body}")"
assert_status "${docs_status}" "200" "${docs_body}"

openapi_body="${WORKDIR}/openapi.json"
openapi_status="$(request GET /openapi.json "" "" "${openapi_body}")"
assert_status "${openapi_status}" "200" "${openapi_body}"
[[ "$(json_field "${openapi_body}" info.title)" == "emr-service" ]] || {
  echo "Unexpected OpenAPI title" >&2
  cat "${openapi_body}" >&2
  exit 1
}

admin_login_body="${WORKDIR}/admin-login.json"
admin_login_status="$(request POST /api/v1/auth/login "{\"username\":\"${ADMIN_LOGIN}\",\"password\":\"${ADMIN_PASSWORD}\"}" "" "${admin_login_body}")"
assert_status "${admin_login_status}" "200" "${admin_login_body}"
admin_token="$(json_field "${admin_login_body}" access_token)"

bad_login_body="${WORKDIR}/bad-login.json"
bad_login_status="$(request POST /api/v1/auth/login "{\"username\":\"${ADMIN_LOGIN}\",\"password\":\"wrong-password\"}" "" "${bad_login_body}")"
assert_status "${bad_login_status}" "401" "${bad_login_body}"

doctor_create_body="${WORKDIR}/doctor-create.json"
doctor_create_status="$(request POST /api/v1/admin/doctors "{\"full_name\":\"Dr. E2E ${suffix}\",\"specialization\":\"Therapist\",\"phone\":\"+7999000${suffix: -4}\",\"email\":\"doctor.${suffix}@example.com\",\"username\":\"doctor_${suffix}\",\"password\":\"DoctorPass123\"}" "${admin_token}" "${doctor_create_body}")"
assert_status "${doctor_create_status}" "201" "${doctor_create_body}"
doctor_id="$(json_field "${doctor_create_body}" id)"

doctor_two_body="${WORKDIR}/doctor-two.json"
doctor_two_status="$(request POST /api/v1/admin/doctors "{\"full_name\":\"Dr. E2E Two ${suffix}\",\"specialization\":\"Cardiologist\",\"phone\":\"+7999111${suffix: -4}\",\"email\":\"doctor.two.${suffix}@example.com\",\"username\":\"doctor_two_${suffix}\",\"password\":\"DoctorPass123\"}" "${admin_token}" "${doctor_two_body}")"
assert_status "${doctor_two_status}" "201" "${doctor_two_body}"

patient_create_body="${WORKDIR}/patient-create.json"
patient_create_status="$(request POST /api/v1/admin/patients "{\"full_name\":\"Patient E2E ${suffix}\",\"date_of_birth\":\"1990-01-10\",\"gender\":\"female\",\"phone\":\"+7888000${suffix: -4}\",\"email\":\"patient.${suffix}@example.com\",\"address\":\"Lenina ${suffix}\",\"insurance_number\":\"POLICY-${suffix}\",\"username\":\"patient_${suffix}\",\"password\":\"PatientPass123\"}" "${admin_token}" "${patient_create_body}")"
assert_status "${patient_create_status}" "201" "${patient_create_body}"
patient_id="$(json_field "${patient_create_body}" id)"

patient_two_body="${WORKDIR}/patient-two.json"
patient_two_status="$(request POST /api/v1/admin/patients "{\"full_name\":\"Patient E2E Two ${suffix}\",\"date_of_birth\":\"1994-05-04\",\"gender\":\"male\",\"phone\":\"+7888111${suffix: -4}\",\"email\":\"patient.two.${suffix}@example.com\",\"address\":\"Nevsky ${suffix}\",\"insurance_number\":\"POLICY-TWO-${suffix}\",\"username\":\"patient_two_${suffix}\",\"password\":\"PatientPass123\"}" "${admin_token}" "${patient_two_body}")"
assert_status "${patient_two_status}" "201" "${patient_two_body}"

duplicate_body="${WORKDIR}/duplicate.json"
duplicate_status="$(request POST /api/v1/admin/doctors "{\"full_name\":\"Dr. Dup ${suffix}\",\"specialization\":\"Therapist\",\"phone\":\"+70000000000\",\"email\":\"doctor.${suffix}@example.com\",\"username\":\"doctor_${suffix}\",\"password\":\"DoctorPass123\"}" "${admin_token}" "${duplicate_body}")"
assert_status "${duplicate_status}" "409" "${duplicate_body}"

doctor_login_body="${WORKDIR}/doctor-login.json"
doctor_login_status="$(request POST /api/v1/auth/login "{\"username\":\"doctor_${suffix}\",\"password\":\"DoctorPass123\"}" "" "${doctor_login_body}")"
assert_status "${doctor_login_status}" "200" "${doctor_login_body}"
doctor_token="$(json_field "${doctor_login_body}" access_token)"
[[ "$(json_field "${doctor_login_body}" profile_id)" == "${doctor_id}" ]] || exit 1

doctor_two_login_body="${WORKDIR}/doctor-two-login.json"
doctor_two_login_status="$(request POST /api/v1/auth/login "{\"username\":\"doctor_two_${suffix}\",\"password\":\"DoctorPass123\"}" "" "${doctor_two_login_body}")"
assert_status "${doctor_two_login_status}" "200" "${doctor_two_login_body}"
doctor_two_token="$(json_field "${doctor_two_login_body}" access_token)"

patient_login_body="${WORKDIR}/patient-login.json"
patient_login_status="$(request POST /api/v1/auth/login "{\"username\":\"patient_${suffix}\",\"password\":\"PatientPass123\"}" "" "${patient_login_body}")"
assert_status "${patient_login_status}" "200" "${patient_login_body}"
patient_token="$(json_field "${patient_login_body}" access_token)"

patient_two_login_body="${WORKDIR}/patient-two-login.json"
patient_two_login_status="$(request POST /api/v1/auth/login "{\"username\":\"patient_two_${suffix}\",\"password\":\"PatientPass123\"}" "" "${patient_two_login_body}")"
assert_status "${patient_two_login_status}" "200" "${patient_two_login_body}"
patient_two_token="$(json_field "${patient_two_login_body}" access_token)"

available_body="${WORKDIR}/available.json"
available_status="$(request GET /api/v1/doctors/me/patients/available "" "${doctor_token}" "${available_body}")"
assert_status "${available_status}" "200" "${available_body}"
python3 - "${available_body}" "${patient_id}" <<'PY'
import json, sys
items = {item["id"] for item in json.load(open(sys.argv[1], encoding="utf-8"))}
if sys.argv[2] not in items:
    raise SystemExit(1)
PY

assign_body="${WORKDIR}/assign.json"
assign_status="$(request POST "/api/v1/doctors/me/patients/${patient_id}/assign" "" "${doctor_token}" "${assign_body}")"
assert_status "${assign_status}" "201" "${assign_body}"

foreign_body="${WORKDIR}/foreign.json"
foreign_status="$(request GET "/api/v1/doctors/me/patients/${patient_id}" "" "${doctor_two_token}" "${foreign_body}")"
assert_status "${foreign_status}" "404" "${foreign_body}"

record_body="${WORKDIR}/record.json"
record_status="$(request POST "/api/v1/doctors/me/patients/${patient_id}/medical-records" "{\"visit_date\":\"2026-04-21T09:00:00Z\",\"complaints\":\"Headache\",\"diagnosis\":\"Migraine\",\"examination_results\":\"Stable vitals\",\"doctor_comment\":\"Hydration and rest\"}" "${doctor_token}" "${record_body}")"
assert_status "${record_status}" "201" "${record_body}"

prescription_body="${WORKDIR}/prescription.json"
prescription_status="$(request POST "/api/v1/doctors/me/patients/${patient_id}/prescriptions" "{\"prescribed_at\":\"2026-04-21T09:30:00Z\",\"title\":\"Ibuprofen\",\"dosage\":\"200 mg\",\"treatment_period\":\"5 days\",\"doctor_comment\":\"After meals\"}" "${doctor_token}" "${prescription_body}")"
assert_status "${prescription_status}" "201" "${prescription_body}"

doctor_list_body="${WORKDIR}/doctor-list.json"
doctor_list_status="$(request GET /api/v1/doctors/me/patients "" "${doctor_token}" "${doctor_list_body}")"
assert_status "${doctor_list_status}" "200" "${doctor_list_body}"
python3 - "${doctor_list_body}" "${patient_id}" <<'PY'
import json, sys
items = json.load(open(sys.argv[1], encoding="utf-8"))
if [item["id"] for item in items] != [sys.argv[2]]:
    raise SystemExit(1)
PY

patient_card_body="${WORKDIR}/patient-card.json"
patient_card_status="$(request GET /api/v1/patients/me "" "${patient_token}" "${patient_card_body}")"
assert_status "${patient_card_status}" "200" "${patient_card_body}"
[[ "$(json_field "${patient_card_body}" personal_data.id)" == "${patient_id}" ]] || exit 1
[[ "$(json_field "${patient_card_body}" medical_records.0.diagnosis)" == "Migraine" ]] || exit 1
[[ "$(json_field "${patient_card_body}" prescriptions.0.title)" == "Ibuprofen" ]] || exit 1

update_body="${WORKDIR}/update.json"
update_status="$(request PATCH /api/v1/patients/me "{\"phone\":\"+79991112233\",\"email\":\"updated.${suffix}@example.com\",\"address\":\"Nevsky prospect 10\"}" "${patient_token}" "${update_body}")"
assert_status "${update_status}" "200" "${update_body}"
[[ "$(json_field "${update_body}" phone)" == "+79991112233" ]] || exit 1

patient_two_card_body="${WORKDIR}/patient-two-card.json"
patient_two_card_status="$(request GET /api/v1/patients/me "" "${patient_two_token}" "${patient_two_card_body}")"
assert_status "${patient_two_card_status}" "200" "${patient_two_card_body}"
python3 - "${patient_two_card_body}" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
if data["medical_records"] or data["prescriptions"]:
    raise SystemExit(1)
PY

rbac_body="${WORKDIR}/rbac.json"
rbac_status="$(request POST /api/v1/admin/doctors "{\"full_name\":\"Blocked\",\"specialization\":\"Therapist\",\"phone\":\"+79990000000\",\"email\":\"blocked.${suffix}@example.com\",\"username\":\"blocked_${suffix}\",\"password\":\"DoctorPass123\"}" "${doctor_token}" "${rbac_body}")"
assert_status "${rbac_status}" "403" "${rbac_body}"

patient_forbidden_body="${WORKDIR}/patient-forbidden.json"
patient_forbidden_status="$(request GET "/api/v1/doctors/me/patients/${patient_id}" "" "${patient_token}" "${patient_forbidden_body}")"
assert_status "${patient_forbidden_status}" "403" "${patient_forbidden_body}"

invalid_payload_body="${WORKDIR}/invalid-payload.json"
invalid_payload_status="$(request POST /api/v1/auth/login "{\"username\":\"ab\",\"password\":\"123\"}" "" "${invalid_payload_body}")"
assert_status "${invalid_payload_status}" "422" "${invalid_payload_body}"

metrics_body="${WORKDIR}/metrics.txt"
metrics_status="$(request GET /metrics "" "" "${metrics_body}")"
assert_status "${metrics_status}" "200" "${metrics_body}"
grep -q "emr_http_requests_total" "${metrics_body}"
grep -q "emr_business_operations_total" "${metrics_body}"

echo "E2E smoke completed successfully against ${BASE_URL}"
