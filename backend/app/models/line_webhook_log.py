from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class LineWebhookLog(Base, TimestampMixin):
    __tablename__ = "line_webhook_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_payload: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
