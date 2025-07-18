import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from sqlalchemy import (
    and_,
    false,
    func,
    insert,
    null,
    or_,
    select,
    text,
    true,
    update,
    literal_column,
    case,
    lateral
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.session import async_session, ro_async_session
from app.models import (
    MessageModel, UserModel, TeamModel, ExternalTransactionModel, BankDetailModel
)
from app.schemas.MessageScheme import *
from app.core.constants import Role

logger = logging.getLogger(__name__)

def get_search_filters(
    filter: MessageRequestScheme
):
    queries_none = [
        MessageModel.offset_id < filter.last_offset_id,
        MessageModel.create_timestamp < datetime.utcfromtimestamp(filter.timestamp_to) if filter.timestamp_to else None,
        MessageModel.create_timestamp > datetime.utcfromtimestamp(filter.timestamp_from) if filter.timestamp_from else None,
        MessageModel.user_id == filter.user_id if filter.user_id else None,
        MessageModel.title == filter.bank if filter.bank else None,
        TeamModel.geo_id == filter.geo_id if filter.geo_id else None,
        MessageModel.external_transaction_id != None if filter.status == True else None,
        MessageModel.external_transaction_id == None if filter.status == False else None,
        or_(
            MessageModel.device_hash == filter.search,
            MessageModel.number == filter.search,
            MessageModel.external_transaction_id == filter.search,
            MessageModel.bank_detail_number == filter.search,
            ExternalTransactionModel.bank_detail_id == filter.search
        ) if filter.search else None
    ]
    queries = []
    for query in queries_none:
        if query is not None:
            queries.append(query)

    return queries

async def get_messages(
        filter: MessageRequestScheme,
        role: str
) -> ListResponse:
    queries = get_search_filters(filter)
    async with ro_async_session() as session:
        query = (
            select(MessageModel, UserModel.name, ExternalTransactionModel.type, BankDetailModel.alias)
            .join(UserModel, MessageModel.user_id == UserModel.id)
            .join(TeamModel, MessageModel.user_id == TeamModel.id)
            .outerjoin(ExternalTransactionModel, MessageModel.external_transaction_id == ExternalTransactionModel.id)
            .outerjoin(BankDetailModel, ExternalTransactionModel.bank_detail_id == BankDetailModel.id)
            .filter(*queries)
            .order_by(MessageModel.create_timestamp.desc())
            .limit(filter.limit)
        )

        list = await session.execute(query)
        result = ListResponse(
            items=[
                Response(
                    **i[0].__dict__,
                    team_name=i[1],
                    type=i[2],
                    alias=i[3] if role == Role.TEAM else None
                )
                for i in list
            ]
        )
        return result
        