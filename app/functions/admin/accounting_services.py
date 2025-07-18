from datetime import datetime, timedelta
from typing import List

from sqlalchemy import Numeric, case, cast, func, select, true, text, or_
from sqlalchemy.orm import aliased

from app.core.constants import ONE_MILLION, Role
from app.core.session import async_session, ro_async_session
from app.models import InternalTransactionModel, UserBalanceChangeModel, UserModel, GeoModel, MerchantModel, TeamModel
from app.schemas.admin.AccountingScheme import (
    ListResponseAccounting,
    FilterAccountingScheme,
    DownloadAccountingScheme,
    ResponseAccountingScheme
)


def get_search_filters(search: str | None):
    if search is None:
        return []
    queries = [or_(
        UserModel.id == search,
        UserModel.name == search
    )]
    return queries

async def get_list_accounting(request: FilterAccountingScheme, namespace_id: int) -> ListResponseAccounting:
    async with ro_async_session() as session:
        user_balance_subq = (
            select(
                UserBalanceChangeModel.balance_id,
                (func.sum(UserBalanceChangeModel.trust_balance) + func.sum(UserBalanceChangeModel.locked_balance)).label("balance"),
            )
            .group_by(UserBalanceChangeModel.balance_id)
            .subquery()
        )

        team_alias = aliased(TeamModel, flat=True)
        merchant_alias = aliased(MerchantModel, flat=True)

        base_query = select(
            UserModel.id,
            UserModel.offset_id,
            UserModel.role,
            UserModel.name,
            UserModel.balance_id
        ).filter(UserModel.namespace_id == namespace_id)

        if request.last_offset_id:
            base_query = base_query.filter(UserModel.offset_id < request.last_offset_id)
        if request.role:
            base_query = base_query.filter(UserModel.role == request.role)
        if request.limit:
            base_query = base_query.limit(request.limit)
        query = get_search_filters(request.search)
        base_query = base_query.filter(*query)
        user_subq = base_query.subquery()

        team_merchant_subq = (
            select(
                user_subq.c.id,
                user_subq.c.offset_id,
                user_subq.c.role,
                user_subq.c.name,
                GeoModel.name.label("geo"),
                user_balance_subq.c.balance,
                func.sum(
                    case(
                        (InternalTransactionModel.status.in_(['pending', 'processing']) &
                         (InternalTransactionModel.direction == 'inbound'),
                         InternalTransactionModel.amount),
                        else_=0
                    )
                ).label("pending_deposit"),
                func.sum(
                    case(
                        (InternalTransactionModel.status.in_(['pending', 'processing']) &
                         (InternalTransactionModel.direction == 'outbound'),
                         InternalTransactionModel.amount),
                        else_=0
                    )
                ).label("pending_withdraw")
            )
            .join(user_balance_subq, user_subq.c.balance_id == user_balance_subq.c.balance_id)
            .outerjoin(team_alias, user_subq.c.id == team_alias.id)
            .outerjoin(merchant_alias, user_subq.c.id == merchant_alias.id)
            .outerjoin(GeoModel, (team_alias.geo_id == GeoModel.id) | (merchant_alias.geo_id == GeoModel.id))
            .outerjoin(InternalTransactionModel, InternalTransactionModel.user_id == user_subq.c.id)
            .group_by(
                user_subq.c.id, user_subq.c.offset_id, user_subq.c.role, user_subq.c.name, GeoModel.name,
                user_balance_subq.c.balance, GeoModel.id
            )
            .order_by(GeoModel.id, user_subq.c.role, user_subq.c.name)
        )

        if request.geo_id and request.role != Role.AGENT:
            team_merchant_subq = team_merchant_subq.filter(GeoModel.id == request.geo_id)

        result = await session.execute(team_merchant_subq)
        users = result.mappings().all()

        return ListResponseAccounting(items=[
            ResponseAccountingScheme(
                id=str(row["id"]),
                offset_id=str(row["offset_id"]),
                role=row["role"],
                name=row["name"],
                geo=row["geo"],
                balance=round(row["balance"] / ONE_MILLION, 2),
                pending_deposit=round(row["pending_deposit"] / ONE_MILLION, 2),
                pending_withdraw=round(row["pending_withdraw"] / ONE_MILLION, 2)
            ) for row in users
        ])

async def get_accounting_user(id: str):
    async with ro_async_session() as session:
        user_balance_subq = (
            select(
                UserBalanceChangeModel.balance_id,
                func.sum(UserBalanceChangeModel.trust_balance).label("trust_balance"),
                func.sum(UserBalanceChangeModel.locked_balance).label("locked_balance")
            )
            .group_by(UserBalanceChangeModel.balance_id)
            .subquery()
        )

        team_alias = aliased(TeamModel, flat=True)
        merchant_alias = aliased(MerchantModel, flat=True)

        team_merchant_subq = (
            select(
                UserModel.balance_id,
                UserModel.role,
                UserModel.name,
                (user_balance_subq.c.trust_balance + user_balance_subq.c.locked_balance).label("balance")
            )
            .join(user_balance_subq, UserModel.balance_id == user_balance_subq.c.balance_id)
            .outerjoin(team_alias, UserModel.id == team_alias.id)
            .outerjoin(merchant_alias, UserModel.id == merchant_alias.id)
            .outerjoin(GeoModel, (team_alias.geo_id == GeoModel.id) | (merchant_alias.geo_id == GeoModel.id))
            .where(UserModel.id == id)
        )
        res = await session.execute(team_merchant_subq)
        users = res.mappings().all()
        name = users[0]["name"]
        balance = round(users[0]["balance"] / ONE_MILLION, 2)
        role = users[0]["role"]
        balance_id = users[0]["balance_id"]

        return name, balance, role, balance_id