from sqlalchemy import select, and_

from app.schemas.UserScheme import UserSupportScheme
from app.models import ExternalTransactionModel, MerchantModel
from app.core.session import ro_async_session, async_session
from app.core.constants import Status, Direction


async def get_banks_filters(current_user: UserSupportScheme, geo_id: str):
    async with ro_async_session() as session:
        return (await session.execute(
            select(ExternalTransactionModel.bank_detail_bank)
            .join(MerchantModel, MerchantModel.id == ExternalTransactionModel.merchant_id)
            .where(
                and_(
                    MerchantModel.namespace_id == current_user.namespace.id,
                    MerchantModel.geo_id == geo_id,
                    ExternalTransactionModel.bank_detail_bank != None,
                    ExternalTransactionModel.status == Status.PENDING,
                    ExternalTransactionModel.direction == Direction.OUTBOUND,
                )
            )
            .distinct()
        )).scalars().all()
