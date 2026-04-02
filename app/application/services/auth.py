from __future__ import annotations

from dataclasses import dataclass

from app.application.ports.repositories import AuthRepository
from app.core.config import Settings
from app.core.metrics import observe_business_operation
from app.core.security import create_access_token, verify_password
from app.core.logging import get_logger
from app.domain.entities import UserAccount
from app.domain.enums import Role
from app.domain.exceptions import AuthenticationError


@dataclass(slots=True)
class LoginResult:
    access_token: str
    token_type: str
    role: Role
    profile_id: str | None


class AuthService:
    def __init__(self, auth_repository: AuthRepository, settings: Settings) -> None:
        self._auth_repository = auth_repository
        self._settings = settings
        self._logger = get_logger(__name__)

    async def login(self, username: str, password: str) -> LoginResult:
        with observe_business_operation("auth", "login", username=username):
            user = await self._auth_repository.get_user_by_username(username)
            if user is None or not user.is_active:
                self._logger.warning("login_failed", extra={"username": username})
                raise AuthenticationError("Invalid username or password.")
            if not verify_password(password, user.password_hash):
                self._logger.warning("login_failed", extra={"username": username})
                raise AuthenticationError("Invalid username or password.")

            profile_id = await self._resolve_profile_id(user)
            access_token = create_access_token(
                {
                    "sub": user.id,
                    "role": user.role.value,
                    "profile_id": profile_id,
                },
                self._settings,
            )
            self._logger.info(
                "login_succeeded",
                extra={"username": username, "role": user.role.value, "profile_id": profile_id},
            )
            return LoginResult(
                access_token=access_token,
                token_type="bearer",
                role=user.role,
                profile_id=profile_id,
            )

    async def _resolve_profile_id(self, user: UserAccount) -> str | None:
        if user.role is Role.DOCTOR:
            doctor = await self._auth_repository.get_doctor_by_user_id(user.id)
            return doctor.id if doctor else None
        if user.role is Role.PATIENT:
            patient = await self._auth_repository.get_patient_by_user_id(user.id)
            return patient.id if patient else None
        return None
