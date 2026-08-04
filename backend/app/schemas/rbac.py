from pydantic import BaseModel


class PermissionOut(BaseModel):
    id: int
    code: str
    description: str | None

    class Config:
        from_attributes = True


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None
    permissions: list[PermissionOut] = []

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    permission_ids: list[int] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permission_ids: list[int] | None = None


class AdminUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    role_ids: list[int] = []


class AdminUserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    password: str | None = None
    role_ids: list[int] | None = None


class AdminUserListOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    roles: list[str] = []

    class Config:
        from_attributes = True


class AdminUserDetailOut(AdminUserListOut):
    role_ids: list[int] = []
