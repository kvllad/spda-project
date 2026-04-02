from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.admin import AdminService
from app.application.services.auth import AuthService
from app.application.services.doctor import DoctorService
from app.application.services.patient import PatientService
from app.core.config import Settings
from app.core.security import decode_access_token
from app.domain.entities import AuthContext
from app.domain.enums import Role
from app.domain.exceptions import AuthenticationError, AuthorizationError
from app.infrastructure.repositories.sqlalchemy import (
    SqlAlchemyAuthRepository,
    SqlAlchemyEmrRepository,
)

security_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.database_manager.session_factory
    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
AuthCredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(security_scheme),
]


def get_auth_service(
    session: SessionDep,
    settings: SettingsDep,
) -> AuthService:
    return AuthService(SqlAlchemyAuthRepository(session), settings)


def get_admin_service(
    session: SessionDep,
) -> AdminService:
    return AdminService(SqlAlchemyAuthRepository(session), SqlAlchemyEmrRepository(session))


def get_doctor_service(
    session: SessionDep,
) -> DoctorService:
    return DoctorService(SqlAlchemyEmrRepository(session))


def get_patient_service(
    session: SessionDep,
) -> PatientService:
    return PatientService(SqlAlchemyEmrRepository(session))


async def get_current_auth_context(
    credentials: AuthCredentialsDep,
    settings: SettingsDep,
) -> AuthContext:
    if credentials is None:
        raise AuthenticationError("Authentication credentials were not provided.")
    payload = decode_access_token(credentials.credentials, settings)
    role = payload.get("role")
    user_id = payload.get("sub")
    if not user_id or not role:
        raise AuthenticationError("Invalid access token payload.")
    return AuthContext(
        user_id=user_id,
        role=Role(role),
        profile_id=payload.get("profile_id"),
    )


def require_roles(*roles: Role) -> Callable[[AuthContext], AuthContext]:
    async def dependency(
        auth_context: Annotated[AuthContext, Depends(get_current_auth_context)],
    ) -> AuthContext:
        if auth_context.role not in roles:
            raise AuthorizationError("You do not have access to this resource.")
        return auth_context

    return dependency
