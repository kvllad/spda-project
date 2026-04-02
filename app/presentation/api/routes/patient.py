from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.patient import PatientService, UpdatePatientProfileCommand
from app.domain.entities import AuthContext
from app.domain.enums import Role
from app.domain.exceptions import AuthenticationError
from app.presentation.api.dependencies import get_patient_service, get_session, require_roles
from app.presentation.api.schemas import PatientCardResponse, PatientResponse, PatientUpdateRequest

router = APIRouter(prefix="/patients/me", tags=["patient"])

PatientAuth = Annotated[AuthContext, Depends(require_roles(Role.PATIENT))]
DbSession = Annotated[AsyncSession, Depends(get_session)]
PatientServiceDep = Annotated[PatientService, Depends(get_patient_service)]


def _patient_id(auth_context: AuthContext) -> str:
    if auth_context.profile_id is None:
        raise AuthenticationError("Patient profile is not linked to the account.")
    return auth_context.profile_id


@router.get("", response_model=PatientCardResponse)
async def get_my_card(
    auth_context: PatientAuth,
    patient_service: PatientServiceDep,
) -> PatientCardResponse:
    card = await patient_service.get_my_card(_patient_id(auth_context))
    return PatientCardResponse.model_validate(card)


@router.patch("", response_model=PatientResponse)
async def update_my_profile(
    payload: PatientUpdateRequest,
    auth_context: PatientAuth,
    session: DbSession,
    patient_service: PatientServiceDep,
) -> PatientResponse:
    patient = await patient_service.update_my_profile(
        UpdatePatientProfileCommand(
            patient_id=_patient_id(auth_context),
            phone=payload.phone,
            email=str(payload.email) if payload.email else None,
            address=payload.address,
        ),
    )
    await session.commit()
    return PatientResponse.model_validate(patient)
