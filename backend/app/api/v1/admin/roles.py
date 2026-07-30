from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_permission
from app.models.rbac import Permission, Role
from app.schemas.rbac import PermissionOut, RoleCreate, RoleOut, RoleUpdate

router = APIRouter(prefix="/roles", tags=["admin-roles"])


@router.get("", response_model=list[RoleOut], dependencies=[Depends(require_permission("roles.read"))])
def list_roles(db: Session = Depends(get_db)) -> list[Role]:
    return db.query(Role).options(selectinload(Role.permissions)).order_by(Role.id).all()


@router.get(
    "/permissions",
    response_model=list[PermissionOut],
    dependencies=[Depends(require_permission("roles.read"))],
)
def list_permissions(db: Session = Depends(get_db)) -> list[Permission]:
    return db.query(Permission).order_by(Permission.code).all()


@router.post(
    "", response_model=RoleOut, status_code=201, dependencies=[Depends(require_permission("roles.write"))]
)
def create_role(payload: RoleCreate, db: Session = Depends(get_db)) -> Role:
    if db.query(Role).filter(Role.name == payload.name).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Role name already exists")
    role = Role(name=payload.name, description=payload.description)
    if payload.permission_ids:
        role.permissions = db.query(Permission).filter(Permission.id.in_(payload.permission_ids)).all()
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.put(
    "/{role_id}", response_model=RoleOut, dependencies=[Depends(require_permission("roles.write"))]
)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db)) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.permission_ids is not None:
        role.permissions = db.query(Permission).filter(Permission.id.in_(payload.permission_ids)).all()
    db.commit()
    return role


@router.delete(
    "/{role_id}", status_code=204, dependencies=[Depends(require_permission("roles.write"))]
)
def delete_role(role_id: int, db: Session = Depends(get_db)) -> None:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Role not found")
    db.delete(role)
    db.commit()
