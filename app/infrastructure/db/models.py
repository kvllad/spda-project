from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import Gender, Role
from app.infrastructure.db.base import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _utc_now() -> datetime:
    return datetime.now(UTC)


class UserAccountModel(Base):
    __tablename__ = "user_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    doctor_profile: Mapped[DoctorModel | None] = relationship(
        back_populates="user",
        uselist=False,
    )
    patient_profile: Mapped[PatientModel | None] = relationship(
        back_populates="user",
        uselist=False,
    )


class DoctorModel(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(String(255))
    specialization: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    user: Mapped[UserAccountModel] = relationship(back_populates="doctor_profile")
    assignments: Mapped[list[DoctorPatientAssignmentModel]] = relationship(
        back_populates="doctor",
    )


class PatientModel(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[date] = mapped_column(Date)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, native_enum=False))
    phone: Mapped[str] = mapped_column(String(32))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    address: Mapped[str] = mapped_column(String(255))
    insurance_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    user: Mapped[UserAccountModel] = relationship(back_populates="patient_profile")
    assignments: Mapped[list[DoctorPatientAssignmentModel]] = relationship(
        back_populates="patient",
    )
    medical_records: Mapped[list[MedicalRecordModel]] = relationship(
        back_populates="patient",
    )
    prescriptions: Mapped[list[PrescriptionModel]] = relationship(
        back_populates="patient",
    )


class DoctorPatientAssignmentModel(Base):
    __tablename__ = "doctor_patient_assignments"
    __table_args__ = (UniqueConstraint("patient_id", name="uq_assignment_patient"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    doctor_id: Mapped[str] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        index=True,
    )
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    doctor: Mapped[DoctorModel] = relationship(back_populates="assignments")
    patient: Mapped[PatientModel] = relationship(back_populates="assignments")


class MedicalRecordModel(Base):
    __tablename__ = "medical_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    doctor_id: Mapped[str] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        index=True,
    )
    visit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    complaints: Mapped[str] = mapped_column(Text)
    diagnosis: Mapped[str] = mapped_column(Text)
    examination_results: Mapped[str] = mapped_column(Text)
    doctor_comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    patient: Mapped[PatientModel] = relationship(back_populates="medical_records")


class PrescriptionModel(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
    )
    doctor_id: Mapped[str] = mapped_column(
        ForeignKey("doctors.id", ondelete="CASCADE"),
        index=True,
    )
    prescribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    title: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str] = mapped_column(String(255))
    treatment_period: Mapped[str] = mapped_column(String(255))
    doctor_comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    patient: Mapped[PatientModel] = relationship(back_populates="prescriptions")
