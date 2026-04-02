from __future__ import annotations


class AppError(Exception):
    status_code = 400


class AuthenticationError(AppError):
    status_code = 401


class AuthorizationError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409
