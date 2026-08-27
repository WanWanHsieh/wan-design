from sqlalchemy.orm import Session

from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementUpdate


def get_announcement(db: Session) -> Announcement:
    announcement = db.query(Announcement).order_by(Announcement.id.asc()).first()
    if announcement is None:
        announcement = Announcement(message="", is_active=False)
        db.add(announcement)
        db.commit()
    return announcement


def update_announcement(db: Session, data: AnnouncementUpdate) -> Announcement:
    announcement = get_announcement(db)
    announcement.message = data.message
    announcement.is_active = data.is_active
    db.commit()
    return announcement
