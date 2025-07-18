from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user
from app.schemas.UserScheme import UserSupportScheme
from app.services import filters_service


router = APIRouter()


@router.get("/banks")
async def get_banks_filters(
    geo_id: int,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user)
):
    return await filters_service.get_banks_filters(current_user, geo_id)
