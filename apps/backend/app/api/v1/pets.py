from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.pet import Pet
from app.models.user import User
from app.schemas.pet import PetCreate, PetRead, PetUpdate

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("", response_model=list[PetRead])
def list_pets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Pet]:
    pets = db.scalars(
        select(Pet)
        .where(Pet.user_id == current_user.id, Pet.deleted_at.is_(None))
        .order_by(Pet.created_at.desc())
    ).all()
    return pets


@router.post("", response_model=PetRead, status_code=status.HTTP_201_CREATED)
def create_pet(
    payload: PetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Pet:
    pet = Pet(
        user_id=current_user.id,
        name=payload.name,
        species=payload.species,
        breed=payload.breed,
        sex=payload.sex,
        date_of_birth=payload.date_of_birth,
        weight_kg=payload.weight_kg,
        allergies=payload.allergies,
        medical_history=payload.medical_history,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


@router.get("/{pet_id}", response_model=PetRead)
def get_pet(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Pet:
    pet = db.scalar(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id, Pet.deleted_at.is_(None))
    )
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
    return pet


@router.put("/{pet_id}", response_model=PetRead)
def update_pet(
    pet_id: str,
    payload: PetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Pet:
    pet = db.scalar(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id, Pet.deleted_at.is_(None))
    )
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(pet, field, value)

    db.commit()
    db.refresh(pet)
    return pet


@router.delete("/{pet_id}")
def delete_pet(
    pet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    pet = db.scalar(
        select(Pet).where(Pet.id == pet_id, Pet.user_id == current_user.id, Pet.deleted_at.is_(None))
    )
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")

    pet.deleted_at = datetime.now(UTC)
    db.commit()
    return {"status": "ok", "message": "Pet archived successfully"}


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"status": "ok", "router": "pets"}
