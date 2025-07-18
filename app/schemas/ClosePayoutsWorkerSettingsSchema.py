from typing import Optional
from pydantic import ConfigDict

from app.schemas.BaseScheme import BaseScheme


class ClosePayoutsWorkerSettingsModelSchema(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    geo_id: Optional[int] = None
    is_enabled: bool
    
    amount_ge: Optional[int] = None
    amount_le: Optional[int] = None

    type_in: Optional[list[str]] = None
    type_not_in: Optional[list[str]] = None

    bank_in: Optional[list[str]] = None
    bank_not_in: Optional[list[str]] = None

    last_seconds: Optional[int] = None
