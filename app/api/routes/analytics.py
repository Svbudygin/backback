from fastapi import APIRouter, Depends, Query

from app.api.deps import v2_get_current_support_user_with_permissions
from app.services import powerbi_service
from app.enums.PermissionEnum import Permission


router = APIRouter()

@router.get('/powerbi')
async def get_power_bi_analytics(
    _ = Depends(v2_get_current_support_user_with_permissions([Permission.VIEW_ANALYTICS])),
    hard_refresh: bool = Query(default=False),
):
    return await powerbi_service.get_powerbi_report_data(hard_refresh)
