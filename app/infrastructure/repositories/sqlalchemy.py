from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import (
    Doctor,
    DoctorPatientAssignment,
    MedicalRecord,
    Patient,
    PatientCard,
    PatientSummary,
    Prescription,
    UserAccount,
)
from app.domain.exceptions import ConflictError
from app.infrastructure.db.models import (
    DoctorModel,
    DoctorPatientAssignmentModel,
    MedicalRecordModel,
    PatientModel,
    PrescriptionModel,
    UserAccountModel,
)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class SqlAlchemyAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_by_username(self, username: str) -> UserAccount | None:
        result = await self._session.execute(
            select(UserAccountModel).where(UserAccountModel.username == username),
        )
        model = result.scalar_one_or_none()
        return _map_user(model) if model else None

    async def get_doctor_by_user_id(self, user_id: str) -> Doctor | None:
        result = await self._session.execute(
            select(DoctorModel).where(DoctorModel.user_id == user_id),
        )
        model = result.scalar_one_or_none()
        return _map_doctor(model) if model else None

    async def get_patient_by_user_id(self, user_id: str) -> Patient | None:
        result = await self._session.execute(
            select(PatientModel).where(PatientModel.user_id == user_id),
        )
        model = result.scalar_one_or_none()
        return _map_patient(model) if model else None

    async def username_exists(self, username: str) -> bool:
        result = await self._session.execute(
            select(UserAccountModel.id).where(UserAccountModel.username == username),
        )
        return result.scalar_one_or_none() is not None

    async def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        role,
    ) -> UserAccount:
        model = UserAccountModel(
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        self._session.add(model)
        await self._session.flush()
        return _map_user(model)


class SqlAlchemyEmrRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def doctor_email_exists(self, email: str) -> bool:
        result = await self._session.execute(
            select(DoctorModel.id).where(DoctorModel.email == email),
        )
        return result.scalar_one_or_none() is not None

    async def patient_email_exists(self, email: str, exclude_patient_id: str | None = None) -> bool:
        query = select(PatientModel.id).where(PatientModel.email == email)
        if exclude_patient_id:
            query = query.where(PatientModel.id != exclude_patient_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none() is not None

    async def insurance_number_exists(self, insurance_number: str) -> bool:
        result = await self._session.execute(
            select(PatientModel.id).where(PatientModel.insurance_number == insurance_number),
        )
        return result.scalar_one_or_none() is not None

    async def create_doctor(
        self,
        *,
        user_id: str,
        full_name: str,
        specialization: str,
        phone: str,
        email: str,
    ) -> Doctor:
        model = DoctorModel(
            user_id=user_id,
            full_name=full_name,
            specialization=specialization,
            phone=phone,
            email=email,
        )
        self._session.add(model)
        await self._session.flush()
        return _map_doctor(model)

    async def create_patient(
        self,
        *,
        user_id: str,
        full_name: str,
        date_of_birth: date,
        gender,
        phone: str,
        email: str,
        address: str,
        insurance_number: str,
    ) -> Patient:
        model = PatientModel(
            user_id=user_id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            phone=phone,
            email=email,
            address=address,
            insurance_number=insurance_number,
        )
        self._session.add(model)
        await self._session.flush()
        return _map_patient(model)

    async def list_doctor_patients(self, doctor_id: str) -> list[PatientSummary]:
        result = await self._session.execute(
            select(
                PatientModel,
                DoctorPatientAssignmentModel.doctor_id,
                func.max(MedicalRecordModel.visit_date),
            )
            .join(
                DoctorPatientAssignmentModel,
                DoctorPatientAssignmentModel.patient_id == PatientModel.id,
            )
            .outerjoin(MedicalRecordModel, MedicalRecordModel.patient_id == PatientModel.id)
            .where(DoctorPatientAssignmentModel.doctor_id == doctor_id)
            .group_by(PatientModel.id, DoctorPatientAssignmentModel.doctor_id)
            .order_by(PatientModel.full_name.asc()),
        )
        rows = result.all()
        return [
            PatientSummary(
                id=patient.id,
                full_name=patient.full_name,
                date_of_birth=patient.date_of_birth,
                insurance_number=patient.insurance_number,
                assigned_doctor_id=assigned_doctor_id,
                status="assigned",
                last_visit_at=_ensure_utc(last_visit_at) if last_visit_at else None,
            )
            for patient, assigned_doctor_id, last_visit_at in rows
        ]

    async def list_unassigned_patients(self) -> list[PatientSummary]:
        result = await self._session.execute(
            select(PatientModel)
            .outerjoin(
                DoctorPatientAssignmentModel,
                DoctorPatientAssignmentModel.patient_id == PatientModel.id,
            )
            .where(DoctorPatientAssignmentModel.id.is_(None))
            .order_by(PatientModel.full_name.asc()),
        )
        patients = result.scalars().all()
        return [
            PatientSummary(
                id=patient.id,
                full_name=patient.full_name,
                date_of_birth=patient.date_of_birth,
                insurance_number=patient.insurance_number,
                assigned_doctor_id=None,
                status="unassigned",
                last_visit_at=None,
            )
            for patient in patients
        ]

    async def assign_patient(self, doctor_id: str, patient_id: str) -> DoctorPatientAssignment:
        patient = await self._session.get(PatientModel, patient_id)
        if patient is None:
            raise ConflictError("Patient does not exist.")

        existing = await self._session.execute(
            select(DoctorPatientAssignmentModel).where(
                DoctorPatientAssignmentModel.patient_id == patient_id,
            ),
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Patient is already assigned to a doctor.")

        model = DoctorPatientAssignmentModel(doctor_id=doctor_id, patient_id=patient_id)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise ValueError("Patient is already assigned to a doctor.") from error
        return _map_assignment(model)

    async def get_doctor_patient_card(
        self,
        doctor_id: str,
        patient_id: str,
    ) -> PatientCard | None:
        result = await self._session.execute(
            select(DoctorPatientAssignmentModel).where(
                DoctorPatientAssignmentModel.doctor_id == doctor_id,
                DoctorPatientAssignmentModel.patient_id == patient_id,
            ),
        )
        assignment = result.scalar_one_or_none()
        if assignment is None:
            return None
        return await self.get_patient_card(patient_id)

    async def get_patient_card(self, patient_id: str) -> PatientCard | None:
        patient_model = await self._session.get(PatientModel, patient_id)
        if patient_model is None:
            return None

        assignment_result = await self._session.execute(
            select(DoctorPatientAssignmentModel).where(
                DoctorPatientAssignmentModel.patient_id == patient_id,
            ),
        )
        assignment = assignment_result.scalar_one_or_none()

        medical_records_result = await self._session.execute(
            select(MedicalRecordModel)
            .where(MedicalRecordModel.patient_id == patient_id)
            .order_by(MedicalRecordModel.visit_date.desc()),
        )
        prescriptions_result = await self._session.execute(
            select(PrescriptionModel)
            .where(PrescriptionModel.patient_id == patient_id)
            .order_by(PrescriptionModel.prescribed_at.desc()),
        )
        medical_records = medical_records_result.scalars().all()
        prescriptions = prescriptions_result.scalars().all()
        last_visit_at = _ensure_utc(medical_records[0].visit_date) if medical_records else None

        return PatientCard(
            personal_data=_map_patient(patient_model),
            assigned_doctor_id=assignment.doctor_id if assignment else None,
            medical_records=[_map_medical_record(item) for item in medical_records],
            prescriptions=[_map_prescription(item) for item in prescriptions],
            last_visit_at=last_visit_at,
        )

    async def add_medical_record(
        self,
        *,
        patient_id: str,
        doctor_id: str,
        visit_date: datetime,
        complaints: str,
        diagnosis: str,
        examination_results: str,
        doctor_comment: str,
    ) -> MedicalRecord:
        model = MedicalRecordModel(
            patient_id=patient_id,
            doctor_id=doctor_id,
            visit_date=_ensure_utc(visit_date),
            complaints=complaints,
            diagnosis=diagnosis,
            examination_results=examination_results,
            doctor_comment=doctor_comment,
        )
        self._session.add(model)
        await self._session.flush()
        return _map_medical_record(model)

    async def add_prescription(
        self,
        *,
        patient_id: str,
        doctor_id: str,
        prescribed_at: datetime,
        title: str,
        dosage: str,
        treatment_period: str,
        doctor_comment: str,
    ) -> Prescription:
        model = PrescriptionModel(
            patient_id=patient_id,
            doctor_id=doctor_id,
            prescribed_at=_ensure_utc(prescribed_at),
            title=title,
            dosage=dosage,
            treatment_period=treatment_period,
            doctor_comment=doctor_comment,
        )
        self._session.add(model)
        await self._session.flush()
        return _map_prescription(model)

    async def update_patient_contact_info(
        self,
        *,
        patient_id: str,
        phone: str | None,
        email: str | None,
        address: str | None,
    ) -> Patient | None:
        patient = await self._session.get(PatientModel, patient_id)
        if patient is None:
            return None
        if phone is not None:
            patient.phone = phone
        if email is not None:
            patient.email = email
        if address is not None:
            patient.address = address
        await self._session.flush()
        return _map_patient(patient)


def _map_user(model: UserAccountModel) -> UserAccount:
    return UserAccount(
        id=model.id,
        username=model.username,
        password_hash=model.password_hash,
        role=model.role,
        is_active=model.is_active,
        created_at=_ensure_utc(model.created_at),
    )


def _map_doctor(model: DoctorModel) -> Doctor:
    return Doctor(
        id=model.id,
        user_id=model.user_id,
        full_name=model.full_name,
        specialization=model.specialization,
        phone=model.phone,
        email=model.email,
        created_at=_ensure_utc(model.created_at),
    )


def _map_patient(model: PatientModel) -> Patient:
    return Patient(
        id=model.id,
        user_id=model.user_id,
        full_name=model.full_name,
        date_of_birth=model.date_of_birth,
        gender=model.gender,
        phone=model.phone,
        email=model.email,
        address=model.address,
        insurance_number=model.insurance_number,
        created_at=_ensure_utc(model.created_at),
    )


def _map_assignment(model: DoctorPatientAssignmentModel) -> DoctorPatientAssignment:
    return DoctorPatientAssignment(
        id=model.id,
        doctor_id=model.doctor_id,
        patient_id=model.patient_id,
        assigned_at=_ensure_utc(model.assigned_at),
    )


def _map_medical_record(model: MedicalRecordModel) -> MedicalRecord:
    return MedicalRecord(
        id=model.id,
        patient_id=model.patient_id,
        doctor_id=model.doctor_id,
        visit_date=_ensure_utc(model.visit_date),
        complaints=model.complaints,
        diagnosis=model.diagnosis,
        examination_results=model.examination_results,
        doctor_comment=model.doctor_comment,
        created_at=_ensure_utc(model.created_at),
    )


def _map_prescription(model: PrescriptionModel) -> Prescription:
    return Prescription(
        id=model.id,
        patient_id=model.patient_id,
        doctor_id=model.doctor_id,
        prescribed_at=_ensure_utc(model.prescribed_at),
        title=model.title,
        dosage=model.dosage,
        treatment_period=model.treatment_period,
        doctor_comment=model.doctor_comment,
        created_at=_ensure_utc(model.created_at),
    )
