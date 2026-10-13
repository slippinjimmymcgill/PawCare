"""PawCare — Auth API endpoints."""


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    generate_password_reset_token,
    get_current_user,
    get_password_hash,
    is_token_revoked,
    remove_password_reset_token,
    revoke_token,
    security,
    verify_password,
    verify_password_reset_token,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserLogin,
    UserRead,
    UserRegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRegisterResponse:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.email)
    return UserRegisterResponse(
        user=UserRead(id=user.id, name=user.name, email=user.email),
        access_token=token,
    )


@router.post("/login", response_model=Token)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.email)
    return Token(access_token=token)


@router.post("/logout")
def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    del db
    token = credentials.credentials
    if is_token_revoked(token):
        return {"status": "ok", "message": "Token already revoked"}
    revoke_token(token)
    return {"status": "ok", "message": "Logged out successfully"}


@router.get("/me", response_model=UserRead)
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead(id=current_user.id, name=current_user.name, email=current_user.email)


@router.post("/password-reset/request")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        return {"status": "ok", "message": "If the email exists, a reset link has been sent"}

    reset_token = generate_password_reset_token(payload.email)
    return {"status": "ok", "message": "Password reset token generated", "reset_token": reset_token}


@router.post("/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> dict[str, str]:
    if not verify_password_reset_token(payload.token, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.scalar(select(User).where(User.email == payload.email))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = get_password_hash(payload.new_password)
    db.commit()
    remove_password_reset_token(payload.token)
    return {"status": "ok", "message": "Password reset successful"}


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"status": "ok", "router": "auth"}
