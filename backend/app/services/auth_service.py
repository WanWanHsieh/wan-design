from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.admin_user import AdminUser, RefreshToken
from app.models.customer import Customer
from app.schemas.auth import TokenResponse


def _issue_tokens(db: Session, subject_type: str, subject_id: int) -> TokenResponse:
    access_token = create_access_token(subject_type, subject_id)
    raw_refresh = generate_refresh_token()
    refresh_token = RefreshToken(
        subject_type=subject_type,
        subject_id=subject_id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        created_at=datetime.now(timezone.utc),
    )
    db.add(refresh_token)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


def register_customer(
    db: Session, email: str, password: str, full_name: str | None, phone: str | None
) -> Customer:
    existing = db.query(Customer).filter(Customer.email == email).first()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    customer = Customer(
        email=email, password_hash=hash_password(password), full_name=full_name, phone=phone
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def login_customer(db: Session, email: str, password: str) -> TokenResponse:
    customer = db.query(Customer).filter(Customer.email == email).first()
    if (
        customer is None
        or customer.deleted_at is not None
        or not verify_password(password, customer.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not customer.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return _issue_tokens(db, "customer", customer.id)


def login_admin(db: Session, email: str, password: str) -> TokenResponse:
    admin_user = db.query(AdminUser).filter(AdminUser.email == email).first()
    if (
        admin_user is None
        or admin_user.deleted_at is not None
        or not verify_password(password, admin_user.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not admin_user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    admin_user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return _issue_tokens(db, "admin_user", admin_user.id)


def refresh_tokens(db: Session, raw_refresh_token: str, expected_subject_type: str) -> TokenResponse:
    token_hash = hash_refresh_token(raw_refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if (
        stored is None
        or stored.subject_type != expected_subject_type
        or stored.revoked_at is not None
        or stored.expires_at < now
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    stored.revoked_at = now
    db.commit()
    return _issue_tokens(db, stored.subject_type, stored.subject_id)
