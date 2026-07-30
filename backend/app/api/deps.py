from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.admin_user import AdminUser
from app.models.customer import Customer

storefront_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/storefront/auth/login", auto_error=False)
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login", auto_error=False)


def _decode_subject(token: str | None, expected_type: str) -> int:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access" or payload.get("subject_type") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    try:
        return int(payload["sub"])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token payload") from exc


def get_current_customer(
    token: str | None = Depends(storefront_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Customer:
    customer_id = _decode_subject(token, "customer")
    customer = db.get(Customer, customer_id)
    if customer is None or not customer.is_active or customer.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Customer not found or inactive")
    return customer


def get_current_admin_user(
    token: str | None = Depends(admin_oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    admin_id = _decode_subject(token, "admin_user")
    admin_user = db.get(AdminUser, admin_id)
    if admin_user is None or not admin_user.is_active or admin_user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Admin user not found or inactive")
    return admin_user


def get_admin_permission_codes(admin_user: AdminUser) -> set[str]:
    codes: set[str] = set()
    for role in admin_user.roles:
        for permission in role.permissions:
            codes.add(permission.code)
    return codes


def require_permission(permission_code: str) -> Callable[[AdminUser], AdminUser]:
    def _checker(admin_user: AdminUser = Depends(get_current_admin_user)) -> AdminUser:
        codes = get_admin_permission_codes(admin_user)
        if permission_code not in codes:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Missing required permission: {permission_code}"
            )
        return admin_user

    return _checker
