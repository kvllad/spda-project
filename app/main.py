from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.domain.exceptions import AppError
from app.infrastructure.bootstrap import bootstrap_admin
from app.infrastructure.db.session import DatabaseManager
from app.presentation.api.routes import admin, auth, doctor, patient
from app.presentation.middleware.observability import ObservabilityMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_admin(app.state.database_manager.session_factory, app.state.settings)
    yield


def create_app(
    settings: Settings | None = None,
    database_manager: DatabaseManager | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_database_manager = database_manager or DatabaseManager(resolved_settings.database_url)
    configure_logging(resolved_settings.log_level, resolved_settings.log_file_path)

    app = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.database_manager = resolved_database_manager

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc)},
        )

    app.include_router(auth.router, prefix=resolved_settings.api_v1_prefix)
    app.include_router(admin.router, prefix=resolved_settings.api_v1_prefix)
    app.include_router(doctor.router, prefix=resolved_settings.api_v1_prefix)
    app.include_router(patient.router, prefix=resolved_settings.api_v1_prefix)
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/healthz", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics", tags=["health"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
