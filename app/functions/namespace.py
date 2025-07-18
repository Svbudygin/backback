from sqlalchemy import select

from app.core.session import ro_async_session
from app.models import GeoModel, CurrencyModel


async def get_wallet_id_by_namespace():
    pass


async def get_currency_for_merchants_by_geo(geo_id: int | None):
    if geo_id is None:
        return []
    async with ro_async_session() as session:
        currencies = (await session.execute(
            select(CurrencyModel.id).join(GeoModel, GeoModel.name == CurrencyModel.name)
            .distinct()
            .where(geo_id == GeoModel.id)
            .where(~CurrencyModel.id.ilike('%system%'))
        )).scalars().all()

        return currencies
