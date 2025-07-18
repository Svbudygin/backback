from sqlalchemy import select
from fastapi import HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import async_session, ro_async_session
from app.models import ClosePayoutsWorkerSettingsModel
from app.schemas.ClosePayoutsWorkerSettingsSchema import ClosePayoutsWorkerSettingsModelSchema


async def get_close_payouts_worker_settings(geo_id: int) -> ClosePayoutsWorkerSettingsModelSchema:
    async with ro_async_session() as session:
        settings = await _get_close_payouts_worker_settings_by_geo_id(session, geo_id)

        if not settings:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="geo_id not found")

        return settings


async def update_close_payouts_worker_settings(
        geo_id: int,
        data: ClosePayoutsWorkerSettingsModelSchema
) -> ClosePayoutsWorkerSettingsModelSchema:
    async with async_session() as session:
        settings = await _get_close_payouts_worker_settings_by_geo_id(session, geo_id)

        if not settings:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="geo_id not found")
        
        for field, value in data.model_dump(exclude_unset=True).items():
            if field != 'geo_id':
                setattr(settings, field, value)
        
        await session.commit()
        await session.refresh(settings)

        return settings


async def _get_close_payouts_worker_settings_by_geo_id(
        session: AsyncSession,
        geo_id: int
) -> ClosePayoutsWorkerSettingsModelSchema | None:
    settings = (await session.execute(
        select(ClosePayoutsWorkerSettingsModel)
        .where(ClosePayoutsWorkerSettingsModel.geo_id == geo_id)
    )).scalar_one_or_none()

    return settings
