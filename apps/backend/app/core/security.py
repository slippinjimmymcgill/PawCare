from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User

settings = get_settings()
security = HTTPBearer()
INVALIDATED_TOKENS: set[str] = set()
PASSWORD_RESET_TOKENS: dict[str, dict[str, Any]] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expires_in = expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = datetime.now(UTC) + expires_in
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:  # pragma: no cover - passed to caller for HTTP response
        raise ValueError("Invalid or expired token") from exc
    email = payload.get("sub")
    if not email:
        raise ValueError("Token payload missing subject")
    return email


def revoke_token(token: str) -> None:
    INVALIDATED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    return token in INVALIDATED_TOKENS


def generate_password_reset_token(email: str) -> str:
    token = jwt.encode(
        {"sub": email, "exp": datetime.now(UTC) + timedelta(minutes=15)},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    PASSWORD_RESET_TOKENS[token] = {"email": email, "expires_at": datetime.now(UTC) + timedelta(minutes=15)}
    return token


def verify_password_reset_token(token: str, email: str) -> bool:
    if token not in PASSWORD_RESET_TOKENS:
        return False
    payload = PASSWORD_RESET_TOKENS[token]
    if payload["email"] != email:
        return False
    if datetime.now(UTC) > payload["expires_at"]:
        PASSWORD_RESET_TOKENS.pop(token, None)
        return False
    return True


def remove_password_reset_token(token: str) -> None:
    PASSWORD_RESET_TOKENS.pop(token, None)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    if is_token_revoked(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")
    try:
        email = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
