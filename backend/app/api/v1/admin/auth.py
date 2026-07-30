from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_admin_permission_codes, get_current_admin_user, get_db
from app.schemas.auth import AdminUserOut, LoginRequest, RefreshRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["admin-auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login_admin(db, payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.refresh_tokens(db, payload.refresh_token, "admin_user")


@router.get("/me", response_model=AdminUserOut)
def me(admin_user=Depends(get_current_admin_user)) -> AdminUserOut:
    permissions = sorted(get_admin_permission_codes(admin_user))
    return AdminUserOut(
        id=admin_user.id,
        email=admin_user.email,
        full_name=admin_user.full_name,
        is_active=admin_user.is_active,
        permissions=permissions,
    )
