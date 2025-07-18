from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user
from app.schemas.ClosePayoutsWorkerSettingsSchema import ClosePayoutsWorkerSettingsModelSchema
from app.services import settings_service


router = APIRouter()


@router.get("/close-payouts-worker/{geo_id}")
async def get_close_payouts_worker_settings(
    geo_id: int,
    _ = Depends(v2_get_current_support_user),
):
    return await settings_service.get_close_payouts_worker_settings(geo_id)


@router.patch("/close-payouts-worker/{geo_id}")
async def update_close_payouts_worker_settings(
    geo_id: int,
    data: ClosePayoutsWorkerSettingsModelSchema,
    _ = Depends(v2_get_current_support_user)
):
    return await settings_service.update_close_payouts_worker_settings(geo_id, data)
