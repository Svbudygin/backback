from app.schemas.BaseScheme import BaseScheme
from datetime import datetime


class TagScheme(BaseScheme):
    id: str
    name: str | None = None
    code: str | None = None
    create_timestamp: datetime | None = None
