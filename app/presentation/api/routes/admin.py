from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.admin import AdminService, CreateDoctorCommand, CreatePatientCommand
from app.domain.enums import Role
from app.domain.entities import AuthContext
from app.presentation.api.dependencies import get_admin_service, get_session, require_roles
from app.presentation.api.schemas import (
    DoctorCreateRequest,
    DoctorResponse,
    PatientCreateRequest,
    PatientResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post(
    "/doctors",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_doctor(
    payload: DoctorCreateRequest,
    response: Response,
    _: AuthContext = Depends(require_roles(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
    admin_service: AdminService = Depends(get_admin_service),
) -> DoctorResponse:
    doctor = await admin_service.create_doctor(
        CreateDoctorCommand(
            full_name=payload.full_name,
            specialization=payload.specialization,
            phone=payload.phone,
            email=str(payload.email),
            username=payload.username,
            password=payload.password,
        ),
    )
    await session.commit()
    response.status_code = status.HTTP_201_CREATED
    return DoctorResponse.model_validate(doctor)


@router.post(
    "/patients",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
    payload: PatientCreateRequest,
    response: Response,
    _: AuthContext = Depends(require_roles(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
    admin_service: AdminService = Depends(get_admin_service),
) -> PatientResponse:
    patient = await admin_service.create_patient(
        CreatePatientCommand(
            full_name=payload.full_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            phone=payload.phone,
            email=str(payload.email),
            address=payload.address,
            insurance_number=payload.insurance_number,
            username=payload.username,
            password=payload.password,
        ),
    )
    await session.commit()
    response.status_code = status.HTTP_201_CREATED
    return PatientResponse.model_validate(patient)
