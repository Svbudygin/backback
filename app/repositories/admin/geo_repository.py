from sqlalchemy import select, update

from app.core.session import async_session, ro_async_session
from app.models.GeoModel import GeoModel
from app.models.UserModel import UserModel
from app.models.MerchantModel import MerchantModel
from app.models.GeoSettingsModel import GeoSettingsModel
from app.schemas.admin.GeoSettingsScheme import (
    UpdateGeoSettings,
    ResponseUpdateGeoSettings
)


async def get_all(namespace_id: int):
    async with ro_async_session() as session:
        result = await session.execute(
            select(GeoModel).order_by(
                GeoModel.name
            )
        )

        return result.scalars().all()

async def set_geo_settings(id: int, request: UpdateGeoSettings) -> ResponseUpdateGeoSettings:
    async with async_session() as session:
        stmt = (
            update(GeoSettingsModel)
            .where(GeoSettingsModel.id == id)
            .values(request.model_dump(exclude_none=True))
            .returning(GeoSettingsModel)
        )
        result = await session.execute(stmt)
        await session.commit()

        updated_row = result.scalar_one()
        return ResponseUpdateGeoSettings.model_validate(updated_row)


async def get_geo_settings(id: int) -> ResponseUpdateGeoSettings:
    async with ro_async_session() as session:
        result = await session.execute(
            select(GeoSettingsModel).where(GeoSettingsModel.id == id)
        )
        row = result.scalar_one()
        return ResponseUpdateGeoSettings.model_validate(row)

