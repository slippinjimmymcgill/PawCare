from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.health_record import HealthRecord
from app.models.medication import Medication
from app.models.pet import Pet
from app.models.user import User
from app.models.vaccination import Vaccination
from app.schemas.attachment import AttachmentUploadResponse
from app.schemas.health_record import (
    HealthRecordCreate,
    HealthRecordRead,
    HealthRecordUpdate,
)
from app.schemas.medication import MedicationCreate, MedicationRead, MedicationUpdate
from app.schemas.vaccination import (
    VaccinationCreate,
    VaccinationRead,
    VaccinationUpdate,
)
from app.services.storage import StorageService, get_storage_service

router = APIRouter(prefix="/records", tags=["records"])


def get_owned_pet_or_404(db: Session, current_user: User, pet_id: str) -> Pet:
    pet = db.scalar(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id, Pet.deleted_at.is_(None))
    )
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
    return pet


@router.get("/pets/{pet_id}/health-records", response_model=list[HealthRecordRead])
def list_health_records(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[HealthRecord]:
    pet = get_owned_pet_or_404(db, current_user, pet_id)
    del pet
    return db.scalars(
        select(HealthRecord)
        .where(HealthRecord.pet_id == pet_id)
        .order_by(HealthRecord.date.desc(), HealthRecord.created_at.desc())
    ).all()


@router.post("/pets/{pet_id}/health-records", response_model=HealthRecordRead, status_code=status.HTTP_201_CREATED)
def create_health_record(
    pet_id: str,
    payload: HealthRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HealthRecord:
    pet = get_owned_pet_or_404(db, current_user, pet_id)
    if payload.type.value == "weight_log" and payload.weight_kg is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Weight logs require weight_kg")

    record = HealthRecord(
        pet_id=pet.id,
        type=payload.type,
        description=payload.description,
        weight_kg=payload.weight_kg,
        date=payload.date,
        attachment_url=payload.attachment_url,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/pets/{pet_id}/health-records/{record_id}", response_model=HealthRecordRead)
def get_health_record(
    pet_id: str,
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HealthRecord:
    get_owned_pet_or_404(db, current_user, pet_id)
    record = db.scalar(
        select(HealthRecord).where(HealthRecord.id == record_id, HealthRecord.pet_id == pet_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record not found")
    return record


@router.put("/pets/{pet_id}/health-records/{record_id}", response_model=HealthRecordRead)
def update_health_record(
    pet_id: str,
    record_id: str,
    payload: HealthRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HealthRecord:
    get_owned_pet_or_404(db, current_user, pet_id)
    record = db.scalar(
        select(HealthRecord).where(HealthRecord.id == record_id, HealthRecord.pet_id == pet_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/pets/{pet_id}/health-records/{record_id}")
def delete_health_record(
    pet_id: str,
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    get_owned_pet_or_404(db, current_user, pet_id)
    record = db.scalar(
        select(HealthRecord).where(HealthRecord.id == record_id, HealthRecord.pet_id == pet_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record not found")

    db.delete(record)
    db.commit()
    return {"status": "ok", "message": "Health record deleted successfully"}


@router.get("/pets/{pet_id}/medications", response_model=list[MedicationRead])
def list_medications(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Medication]:
    get_owned_pet_or_404(db, current_user, pet_id)
    return db.scalars(
        select(Medication)
        .where(Medication.pet_id == pet_id)
        .order_by(Medication.start_date.desc(), Medication.created_at.desc())
    ).all()


@router.post("/pets/{pet_id}/medications", response_model=MedicationRead, status_code=status.HTTP_201_CREATED)
def create_medication(
    pet_id: str,
    payload: MedicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medication:
    pet = get_owned_pet_or_404(db, current_user, pet_id)
    medication = Medication(
        pet_id=pet.id,
        name=payload.name,
        dosage=payload.dosage,
        frequency=payload.frequency,
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
    )
    db.add(medication)
    db.commit()
    db.refresh(medication)
    return medication


@router.get("/pets/{pet_id}/medications/{medication_id}", response_model=MedicationRead)
def get_medication(
    pet_id: str,
    medication_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medication:
    get_owned_pet_or_404(db, current_user, pet_id)
    medication = db.scalar(
        select(Medication).where(Medication.id == medication_id, Medication.pet_id == pet_id)
    )
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    return medication


@router.put("/pets/{pet_id}/medications/{medication_id}", response_model=MedicationRead)
def update_medication(
    pet_id: str,
    medication_id: str,
    payload: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Medication:
    get_owned_pet_or_404(db, current_user, pet_id)
    medication = db.scalar(
        select(Medication).where(Medication.id == medication_id, Medication.pet_id == pet_id)
    )
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(medication, field, value)

    db.commit()
    db.refresh(medication)
    return medication


@router.delete("/pets/{pet_id}/medications/{medication_id}")
def delete_medication(
    pet_id: str,
    medication_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    get_owned_pet_or_404(db, current_user, pet_id)
    medication = db.scalar(
        select(Medication).where(Medication.id == medication_id, Medication.pet_id == pet_id)
    )
    if medication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    db.delete(medication)
    db.commit()
    return {"status": "ok", "message": "Medication deleted successfully"}


@router.get("/pets/{pet_id}/vaccinations", response_model=list[VaccinationRead])
def list_vaccinations(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Vaccination]:
    get_owned_pet_or_404(db, current_user, pet_id)
    return db.scalars(
        select(Vaccination)
        .where(Vaccination.pet_id == pet_id)
        .order_by(Vaccination.administered_date.desc().nullslast(), Vaccination.created_at.desc())
    ).all()


@router.post("/pets/{pet_id}/vaccinations", response_model=VaccinationRead, status_code=status.HTTP_201_CREATED)
def create_vaccination(
    pet_id: str,
    payload: VaccinationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vaccination:
    pet = get_owned_pet_or_404(db, current_user, pet_id)
    vaccination = Vaccination(
        pet_id=pet.id,
        vaccine_name=payload.vaccine_name,
        administered_date=payload.administered_date,
        next_due_date=payload.next_due_date,
        notes=payload.notes,
    )
    db.add(vaccination)
    db.commit()
    db.refresh(vaccination)
    return vaccination


@router.get("/pets/{pet_id}/vaccinations/{vaccination_id}", response_model=VaccinationRead)
def get_vaccination(
    pet_id: str,
    vaccination_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vaccination:
    get_owned_pet_or_404(db, current_user, pet_id)
    vaccination = db.scalar(
        select(Vaccination).where(Vaccination.id == vaccination_id, Vaccination.pet_id == pet_id)
    )
    if vaccination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")
    return vaccination


@router.put("/pets/{pet_id}/vaccinations/{vaccination_id}", response_model=VaccinationRead)
def update_vaccination(
    pet_id: str,
    vaccination_id: str,
    payload: VaccinationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Vaccination:
    get_owned_pet_or_404(db, current_user, pet_id)
    vaccination = db.scalar(
        select(Vaccination).where(Vaccination.id == vaccination_id, Vaccination.pet_id == pet_id)
    )
    if vaccination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(vaccination, field, value)

    db.commit()
    db.refresh(vaccination)
    return vaccination


@router.delete("/pets/{pet_id}/vaccinations/{vaccination_id}")
def delete_vaccination(
    pet_id: str,
    vaccination_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    get_owned_pet_or_404(db, current_user, pet_id)
    vaccination = db.scalar(
        select(Vaccination).where(Vaccination.id == vaccination_id, Vaccination.pet_id == pet_id)
    )
    if vaccination is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination not found")

    db.delete(vaccination)
    db.commit()
    return {"status": "ok", "message": "Vaccination deleted successfully"}


@router.post(
    "/pets/{pet_id}/attachments",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    pet_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> AttachmentUploadResponse:
    get_owned_pet_or_404(db, current_user, pet_id)
    return await storage_service.validate_and_save(file)


@router.post(
    "/pets/{pet_id}/health-records/{record_id}/attachment",
    response_model=HealthRecordRead,
)
async def attach_file_to_record(
    pet_id: str,
    record_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage_service: StorageService = Depends(get_storage_service),
) -> HealthRecord:
    get_owned_pet_or_404(db, current_user, pet_id)
    record = db.scalar(
        select(HealthRecord).where(HealthRecord.id == record_id, HealthRecord.pet_id == pet_id)
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health record not found")

    upload_res = await storage_service.validate_and_save(file)
    record.attachment_url = upload_res.url
    db.commit()
    db.refresh(record)
    return record


@router.get("/attachments/{filename}")
def get_attachment(
    filename: str,
    storage_service: StorageService = Depends(get_storage_service),
) -> FileResponse:
    file_path = storage_service.get_file_path(filename)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    return FileResponse(file_path)


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"status": "ok", "router": "records"}

