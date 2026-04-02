from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.doctor import (
    CreateMedicalRecordCommand,
    CreatePrescriptionCommand,
    DoctorService,
)
from app.domain.entities import AuthContext
from app.domain.enums import Role
from app.domain.exceptions import AuthenticationError
from app.presentation.api.dependencies import get_doctor_service, get_session, require_roles
from app.presentation.api.schemas import (
    AssignmentResponse,
    MedicalRecordCreateRequest,
    MedicalRecordResponse,
    PatientCardResponse,
    PatientSummaryResponse,
    PrescriptionCreateRequest,
    PrescriptionResponse,
)

router = APIRouter(prefix="/doctors/me", tags=["doctor"])


def _doctor_id(auth_context: AuthContext) -> str:
    if auth_context.profile_id is None:
        raise AuthenticationError("Doctor profile is not linked to the account.")
    return auth_context.profile_id


@router.get("/patients", response_model=list[PatientSummaryResponse])
async def list_patients(
    auth_context: AuthContext = Depends(require_roles(Role.DOCTOR)),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> list[PatientSummaryResponse]:
    patients = await doctor_service.list_patients(_doctor_id(auth_context))
    return [PatientSummaryResponse.model_validate(item) for item in patients]


@router.get("/patients/available", response_model=list[PatientSummaryResponse])
async def list_available_patients(
    _: AuthContext = Depends(require_roles(Role.DOCTOR)),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> list[PatientSummaryResponse]:
    patients = await doctor_service.list_available_patients()
    return [PatientSummaryResponse.model_validate(item) for item in patients]


@router.post(
    "/patients/{patient_id}/assign",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_patient(
    patient_id: str,
    response: Response,
    auth_context: AuthContext = Depends(require_roles(Role.DOCTOR)),
    session: AsyncSession = Depends(get_session),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> AssignmentResponse:
    assignment = await doctor_service.assign_patient(_doctor_id(auth_context), patient_id)
    await session.commit()
    response.status_code = status.HTTP_201_CREATED
    return AssignmentResponse.model_validate(assignment)


@router.get("/patients/{patient_id}", response_model=PatientCardResponse)
async def get_patient_card(
    patient_id: str,
    auth_context: AuthContext = Depends(require_roles(Role.DOCTOR)),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> PatientCardResponse:
    card = await doctor_service.get_patient_card(_doctor_id(auth_context), patient_id)
    return PatientCardResponse.model_validate(card)


@router.post(
    "/patients/{patient_id}/medical-records",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_medical_record(
    patient_id: str,
    payload: MedicalRecordCreateRequest,
    response: Response,
    auth_context: AuthContext = Depends(require_roles(Role.DOCTOR)),
    session: AsyncSession = Depends(get_session),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> MedicalRecordResponse:
    record = await doctor_service.add_medical_record(
        CreateMedicalRecordCommand(
            patient_id=patient_id,
            doctor_id=_doctor_id(auth_context),
            visit_date=payload.visit_date,
            complaints=payload.complaints,
            diagnosis=payload.diagnosis,
            examination_results=payload.examination_results,
            doctor_comment=payload.doctor_comment,
        ),
    )
    await session.commit()
    response.status_code = status.HTTP_201_CREATED
    return MedicalRecordResponse.model_validate(record)


@router.post(
    "/patients/{patient_id}/prescriptions",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_prescription(
    patient_id: str,
    payload: PrescriptionCreateRequest,
    response: Response,
    auth_context: AuthContext = Depends(require_roles(Role.DOCTOR)),
    session: AsyncSession = Depends(get_session),
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> PrescriptionResponse:
    prescription = await doctor_service.add_prescription(
        CreatePrescriptionCommand(
            patient_id=patient_id,
            doctor_id=_doctor_id(auth_context),
            prescribed_at=payload.prescribed_at,
            title=payload.title,
            dosage=payload.dosage,
            treatment_period=payload.treatment_period,
            doctor_comment=payload.doctor_comment,
        ),
    )
    await session.commit()
    response.status_code = status.HTTP_201_CREATED
    return PrescriptionResponse.model_validate(prescription)
