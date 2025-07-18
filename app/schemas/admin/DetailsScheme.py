from typing import Optional

from app.schemas.BaseScheme import BaseScheme
from app.schemas.UserScheme import UserScheme
from app.schemas.BankDetailScheme import *
from app.schemas.BaseScheme import BaseScheme, str_big_factory, str_small_factory, num_factory
from typing import List, Tuple
import datetime

class AdminBankDetailSchemeRequestList(BankDetailSchemeRequestList):
    team_id: str | None = str_small_factory(None)
    period: int | None = num_factory(None)
    geo_id: int | None = num_factory(None)
    type: str | None = str_small_factory(None)

class AdminBankDetailSchemeResponse(BankDetailSchemeResponse):
    team_name: str | None = str_small_factory(None)
    conv: int | None = num_factory(None)
    accepted: int | None = num_factory(None)
    closed: int | None = num_factory(None)
    pending_count: int | None = num_factory(None)
class BankDetailSchemeResponseList(BaseScheme):
    items: List[AdminBankDetailSchemeResponse]

class AdminUpdateDetailRequestScheme(BaseScheme):
    is_active: bool | None = None
    is_vip: bool | None = None
    max_vip_payers: int | None = num_factory(None)
    fiat_max_inbound: int | None = num_factory(None)
    fiat_min_inbound: int | None = num_factory(None)


