from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_permission
from app.core.security import hash_password
from app.models.admin_user import AdminUser
from app.models.rbac import Role
from app.schemas.rbac import AdminUserCreate, AdminUserListOut

router = APIRouter(prefix="/users", tags=["admin-users"])


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
    return [
        AdminUserListOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            is_active=u.is_active,
            roles=[r.name for r in u.roles],
        )
        for u in users
    ]


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
    return AdminUserListOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        roles=[r.name for r in user.roles],
    )
