from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.schemas.announcement import AnnouncementOut, AnnouncementUpdate
from app.services import announcement_service

router = APIRouter(prefix="/announcement", tags=["admin-announcement"])


@router.get(
    "", response_model=AnnouncementOut, dependencies=[Depends(require_permission("settings.read"))]
)
def get_announcement(db: Session = Depends(get_db)):
    return announcement_service.get_announcement(db)


@router.put(
    "", response_model=AnnouncementOut, dependencies=[Depends(require_permission("settings.write"))]
)
def update_announcement(payload: AnnouncementUpdate, db: Session = Depends(get_db)):
    return announcement_service.update_announcement(db, payload)
