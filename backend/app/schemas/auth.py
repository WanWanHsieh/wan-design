from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class CustomerRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    phone: str | None = None


class CustomerOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    phone: str | None

    class Config:
        from_attributes = True


class AdminUserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    permissions: list[str] = []

    class Config:
        from_attributes = True


class AdminSelfUpdateRequest(BaseModel):
    current_password: str
    email: EmailStr | None = None
    full_name: str | None = None
    new_password: str | None = None
