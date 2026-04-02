from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.services.auth import AuthService
from app.presentation.api.dependencies import get_auth_service
from app.presentation.api.schemas import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: TokenRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    result = await auth_service.login(payload.username, payload.password)
    return TokenResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        role=result.role,
        profile_id=result.profile_id,
    )
