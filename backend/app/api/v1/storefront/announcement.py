from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.announcement import AnnouncementPublicOut
from app.services import announcement_service

router = APIRouter(prefix="/announcement", tags=["storefront-announcement"])


@router.get("", response_model=AnnouncementPublicOut)
def get_announcement(db: Session = Depends(get_db)):
    return announcement_service.get_announcement(db)
