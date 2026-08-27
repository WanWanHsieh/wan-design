from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementUpdate(BaseModel):
    message: str = Field(default="", max_length=2000)
    is_active: bool = False


class AnnouncementOut(BaseModel):
    id: int
    message: str
    is_active: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementPublicOut(BaseModel):
    message: str
    is_active: bool

    class Config:
        from_attributes = True
