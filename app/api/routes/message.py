from fastapi import APIRouter, Depends, status

from app import exceptions
from app.api import deps
from app.api.deps import v2_get_current_user
from app.core.constants import Role

from app.schemas.UserScheme import *
from app.schemas.MessageScheme import *
from app.functions.message import *

router = APIRouter()

@router.get("/list")
async def get_list_message(
    last_offset_id: int,
    limit: int,
    create_timestamp_from: int | None = None,
    create_timestamp_to: int | None = None,
    user_id: str | None = None,
    geo_id: str | None = None,
    search: str | None = None,
    bank: str | None = None,
    status: bool | None = None,
    current_user: User = Depends(v2_get_current_user),
) -> ListResponse:
    filter = MessageRequestScheme(
        last_offset_id = last_offset_id,
        limit = limit,
        timestamp_from = create_timestamp_from,
        timestamp_to = create_timestamp_to,
        user_id = user_id,
        geo_id = geo_id,
        search = search,
        bank = bank,
        status=status
    )
    if current_user.role != Role.SUPPORT:
        filter.user_id = current_user.id
    return await get_messages(filter, current_user.role)