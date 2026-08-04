from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_admin_permission_codes, get_current_admin_user, get_db
from app.schemas.auth import AdminSelfUpdateRequest, AdminUserOut, LoginRequest, RefreshRequest, TokenResponse
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


@router.put("/me", response_model=AdminUserOut)
def update_me(
    payload: AdminSelfUpdateRequest,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
) -> AdminUserOut:
    updated = auth_service.update_admin_self(
        db,
        admin_user,
        current_password=payload.current_password,
        email=payload.email,
        full_name=payload.full_name,
        new_password=payload.new_password,
    )
    permissions = sorted(get_admin_permission_codes(updated))
    return AdminUserOut(
        id=updated.id,
        email=updated.email,
        full_name=updated.full_name,
        is_active=updated.is_active,
        permissions=permissions,
    )
