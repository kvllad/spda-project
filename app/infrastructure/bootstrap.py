from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.enums import Role
from app.infrastructure.db.models import UserAccountModel


async def bootstrap_admin(
    session_factory: async_sessionmaker,
    settings: Settings,
) -> None:
    async with session_factory() as session:
        result = await session.execute(
            select(UserAccountModel).where(UserAccountModel.username == settings.admin_login),
        )
        if result.scalar_one_or_none() is None:
            session.add(
                UserAccountModel(
                    username=settings.admin_login,
                    password_hash=hash_password(settings.admin_password),
                    role=Role.ADMIN,
                    is_active=True,
                ),
            )
            await session.commit()
