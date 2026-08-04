from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.core.security import hash_password
from app.models.admin_user import AdminUser
from app.models.rbac import Role
from app.schemas.rbac import AdminUserCreate, AdminUserDetailOut, AdminUserListOut, AdminUserUpdate

router = APIRouter(prefix="/users", tags=["admin-users"])


def _to_list_out(user: AdminUser) -> AdminUserListOut:
    return AdminUserListOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[r.name for r in user.roles],
    )


def _get_active_user(db: Session, user_id: int) -> AdminUser:
    user = db.get(AdminUser, user_id)
    if user is None or user.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.get(
    "", response_model=list[AdminUserListOut], dependencies=[Depends(require_permission("users.read"))]
)
def list_admin_users(db: Session = Depends(get_db)) -> list[AdminUserListOut]:
    users = (
        db.query(AdminUser)
        .options(selectinload(AdminUser.roles))
        .filter(AdminUser.deleted_at.is_(None))
        .order_by(AdminUser.id)
        .all()
    )
    return [_to_list_out(u) for u in users]


@router.get(
    "/{user_id}", response_model=AdminUserDetailOut,
    dependencies=[Depends(require_permission("users.read"))],
)
def get_admin_user(user_id: int, db: Session = Depends(get_db)) -> AdminUserDetailOut:
    user = _get_active_user(db, user_id)
    base = _to_list_out(user)
    return AdminUserDetailOut(**base.model_dump(), role_ids=[r.id for r in user.roles])


@router.post(
    "", response_model=AdminUserListOut, status_code=201,
    dependencies=[Depends(require_permission("users.write"))],
)
def create_admin_user(payload: AdminUserCreate, db: Session = Depends(get_db)) -> AdminUserListOut:
    if db.query(AdminUser).filter(AdminUser.email == payload.email).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
    user = AdminUser(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    if payload.role_ids:
        user.roles = db.query(Role).filter(Role.id.in_(payload.role_ids)).all()
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_list_out(user)


@router.put(
    "/{user_id}", response_model=AdminUserListOut,
    dependencies=[Depends(require_permission("users.write"))],
)
def update_admin_user(
    user_id: int, payload: AdminUserUpdate, db: Session = Depends(get_db)
) -> AdminUserListOut:
    user = _get_active_user(db, user_id)

    if payload.email and payload.email != user.email:
        existing = db.query(AdminUser).filter(AdminUser.email == payload.email).first()
        if existing is not None and existing.id != user.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Email already exists")
        user.email = payload.email

    if payload.full_name:
        user.full_name = payload.full_name

    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.password:
        user.password_hash = hash_password(payload.password)

    if payload.role_ids is not None:
        user.roles = db.query(Role).filter(Role.id.in_(payload.role_ids)).all()

    db.commit()
    db.refresh(user)
    return _to_list_out(user)


@router.delete(
    "/{user_id}", status_code=204, dependencies=[Depends(require_permission("users.write"))]
)
def delete_admin_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
) -> None:
    if user_id == current_admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能刪除自己的帳號")
    user = _get_active_user(db, user_id)
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()
