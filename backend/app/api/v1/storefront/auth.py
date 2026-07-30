from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_customer, get_db
from app.schemas.auth import (
    CustomerOut,
    CustomerRegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["storefront-auth"])


@router.post("/register", response_model=CustomerOut, status_code=201)
def register(payload: CustomerRegisterRequest, db: Session = Depends(get_db)) -> CustomerOut:
    customer = auth_service.register_customer(
        db, payload.email, payload.password, payload.full_name, payload.phone
    )
    return customer


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login_customer(db, payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.refresh_tokens(db, payload.refresh_token, "customer")


@router.get("/me", response_model=CustomerOut)
def me(customer=Depends(get_current_customer)) -> CustomerOut:
    return customer
