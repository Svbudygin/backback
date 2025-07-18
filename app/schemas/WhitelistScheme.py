from app.schemas.BaseScheme import BaseScheme
from typing import List

class WhiteListPayerAddRequest(BaseScheme):
    payer_ids: List[str]
