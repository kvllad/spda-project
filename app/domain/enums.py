from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
