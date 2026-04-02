"""Initial schema.

Revision ID: 20260402_000001
Revises:
Create Date: 2026-04-02 21:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_000001"
down_revision = None
branch_labels = None
depends_on = None


role_enum = sa.Enum("admin", "doctor", "patient", name="role", native_enum=False)
gender_enum = sa.Enum("male", "female", "other", name="gender", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_accounts_username", "user_accounts", ["username"], unique=True)

    op.create_table(
        "doctors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("specialization", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_doctors_email", "doctors", ["email"], unique=True)

    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("user_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", gender_enum, nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("insurance_number", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_patients_email", "patients", ["email"], unique=True)
    op.create_index("ix_patients_insurance_number", "patients", ["insurance_number"], unique=True)

    op.create_table(
        "doctor_patient_assignments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("doctor_id", sa.String(length=36), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("patient_id", name="uq_assignment_patient"),
    )
    op.create_index(
        "ix_doctor_patient_assignments_doctor_id",
        "doctor_patient_assignments",
        ["doctor_id"],
        unique=False,
    )
    op.create_index(
        "ix_doctor_patient_assignments_patient_id",
        "doctor_patient_assignments",
        ["patient_id"],
        unique=False,
    )

    op.create_table(
        "medical_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doctor_id", sa.String(length=36), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visit_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("complaints", sa.Text(), nullable=False),
        sa.Column("diagnosis", sa.Text(), nullable=False),
        sa.Column("examination_results", sa.Text(), nullable=False),
        sa.Column("doctor_comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_medical_records_patient_id", "medical_records", ["patient_id"], unique=False)
    op.create_index("ix_medical_records_doctor_id", "medical_records", ["doctor_id"], unique=False)
    op.create_index("ix_medical_records_visit_date", "medical_records", ["visit_date"], unique=False)

    op.create_table(
        "prescriptions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("patient_id", sa.String(length=36), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doctor_id", sa.String(length=36), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prescribed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("dosage", sa.String(length=255), nullable=False),
        sa.Column("treatment_period", sa.String(length=255), nullable=False),
        sa.Column("doctor_comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prescriptions_patient_id", "prescriptions", ["patient_id"], unique=False)
    op.create_index("ix_prescriptions_doctor_id", "prescriptions", ["doctor_id"], unique=False)
    op.create_index("ix_prescriptions_prescribed_at", "prescriptions", ["prescribed_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_prescriptions_prescribed_at", table_name="prescriptions")
    op.drop_index("ix_prescriptions_doctor_id", table_name="prescriptions")
    op.drop_index("ix_prescriptions_patient_id", table_name="prescriptions")
    op.drop_table("prescriptions")

    op.drop_index("ix_medical_records_visit_date", table_name="medical_records")
    op.drop_index("ix_medical_records_doctor_id", table_name="medical_records")
    op.drop_index("ix_medical_records_patient_id", table_name="medical_records")
    op.drop_table("medical_records")

    op.drop_index("ix_doctor_patient_assignments_patient_id", table_name="doctor_patient_assignments")
    op.drop_index("ix_doctor_patient_assignments_doctor_id", table_name="doctor_patient_assignments")
    op.drop_table("doctor_patient_assignments")

    op.drop_index("ix_patients_insurance_number", table_name="patients")
    op.drop_index("ix_patients_email", table_name="patients")
    op.drop_table("patients")

    op.drop_index("ix_doctors_email", table_name="doctors")
    op.drop_table("doctors")

    op.drop_index("ix_user_accounts_username", table_name="user_accounts")
    op.drop_table("user_accounts")
