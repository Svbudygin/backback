from typing import List
from sqlalchemy import and_, select, true, false, delete, func, or_
from sqlalchemy.orm import aliased
from app import exceptions as exceptions

from app.core.constants import Role, DETAILS_INFO
from app.core.session import async_session
from app.models import FeeContractModel, UserModel, TagModel, BankDetailModel, TeamModel, MerchantModel
from app.schemas.admin.FeeContractScheme import FeeContractResponse
from app.schemas.UserScheme import get_user_scheme, UserMerchantWithTypeResponseScheme
from collections import defaultdict


async def  filter_users_in_namespace_repo(*, geo_id: int | None = None, role: str | None = None, namespace_id: int):
    async with async_session() as session:
        result = (await session.execute(
            select(UserModel).where(
                and_(
                    UserModel.role == role if role is not None else UserModel.role.in_(
                        [Role.MERCHANT, Role.TEAM, Role.AGENT]
                    ),
                    UserModel.namespace_id == namespace_id,
                    UserModel.is_blocked == false(),
                )
            ).order_by(UserModel.name)
        )).scalars().all()

        users = [get_user_scheme(item) for item in result]

        if geo_id is not None:
            users = [user for user in users if
                     (hasattr(user, 'geo') and user.geo is not None and user.geo.id == geo_id) or (
                                 user.role == Role.AGENT)]
        if role == 'merchant':
            return list(map(
                lambda user: UserMerchantWithTypeResponseScheme.model_validate(
                    {**user.model_dump(), "types": DETAILS_INFO.get(user.currency.name, {}).get("types", [])}
                ), users))

        return users


async def filter_fee_contracts_repo(
        *, merchant_id: str, team_id: str, tag_id: str, namespace_id: int
) -> [List[str], List[FeeContractResponse]]:
    async with async_session() as session:
        result = await session.execute(
            select(
                FeeContractModel.id.label("id"),
                FeeContractModel.inbound_fee.label("inbound_fee"),
                FeeContractModel.outbound_fee.label("outbound_fee"),
                FeeContractModel.create_timestamp.label("create_timestamp"),
                FeeContractModel.user_id,
                FeeContractModel.tag_id,
                UserModel.role.label("role"),
                UserModel.name,
                TagModel.name.label("tag_name")
            )
            .join(UserModel, FeeContractModel.user_id == UserModel.id)
            .outerjoin(TagModel, FeeContractModel.tag_id == TagModel.id)
            .where(
                and_(
                    FeeContractModel.merchant_id == merchant_id,
                    FeeContractModel.team_id == team_id,
                    UserModel.namespace_id == namespace_id,
                    FeeContractModel.tag_id == tag_id
                )
            )
        )
        fee_contracts = result.all()
        result = [
            FeeContractResponse(
                id=row.id,
                inbound_fee=row.inbound_fee,
                outbound_fee=row.outbound_fee,
                create_timestamp=row.create_timestamp,
                user_id=row.user_id,
                role=row.role,
                name=row.name,
                tag_id=row.tag_id,
                tag_name=row.tag_name
            )
            for row in fee_contracts
        ]
        types_result = await session.execute(
            select(BankDetailModel.type).distinct().where(
                and_(
                    BankDetailModel.is_active == true(),
                    BankDetailModel.team_id == team_id
                )
            )
        )
        types = [row.type for row in types_result]
        order = {Role.MERCHANT: 0, Role.TEAM: 1, Role.AGENT: 2}
        result.sort(key=lambda x: order[x.role])
        return [types, result]


async def make_copy_fee_contracts(
    merchant_id_from: str,
    merchant_id_to: str,
    tag_id: str | None = None
) -> None:
    async with async_session() as session:
        query = select(FeeContractModel).where(
            FeeContractModel.merchant_id == merchant_id_from
        ).filter(FeeContractModel.is_deleted == false())
        if tag_id:
            query = query.where(FeeContractModel.tag_id == tag_id)

        result = await session.execute(query)
        contracts = result.scalars().all()

        if not contracts:
            return

        delete_stmt = delete(FeeContractModel).where(
            FeeContractModel.merchant_id == merchant_id_to
        )
        if tag_id:
            delete_stmt = delete_stmt.where(FeeContractModel.tag_id == tag_id)
        await session.execute(delete_stmt)

        new_contracts = []
        for contract in contracts:
            new_contracts.append(
                FeeContractModel(
                    merchant_id=merchant_id_to,
                    team_id=contract.team_id,
                    user_id=merchant_id_to if contract.user_id == merchant_id_from else contract.user_id,
                    inbound_fee=contract.inbound_fee,
                    outbound_fee=contract.outbound_fee,
                    is_deleted=False,
                    tag_id=contract.tag_id
                )
            )

        session.add_all(new_contracts)
        await session.commit()


async def validate_fee_total(session, contracts: list[FeeContractModel], fee_column: str, expected_total: int = 10000):
    if not contracts:
        return

    keys = {(c.merchant_id, c.team_id, c.tag_id) for c in contracts}

    conditions = []
    for m_id, t_id, tag in keys:
        cond = (
            (FeeContractModel.merchant_id == m_id) &
            (FeeContractModel.team_id == t_id) &
            (FeeContractModel.tag_id == tag)
        )
        conditions.append(cond)

    query = (
        select(
            FeeContractModel.merchant_id,
            FeeContractModel.team_id,
            FeeContractModel.tag_id,
            func.sum(getattr(FeeContractModel, fee_column))
        )
        .where(FeeContractModel.is_deleted == False)
        .where(or_(*conditions))
        .group_by(FeeContractModel.merchant_id, FeeContractModel.team_id, FeeContractModel.tag_id)
    )

    result = await session.execute(query)
    rows = result.all()

    for merchant_id, team_id, tag_id, total in rows:
        if total != expected_total:
            raise exceptions.FeeSumException()


async def bulk_fee_change(
        delta: int,
        direction: str,
        increase_id: str | None = None,
        decrease_id: str | None = None,
        merchant_id: str | None = None,
        tag_id: str | None = None
) -> None:
    async with async_session() as session:
        async with session.begin():
            increase_role = None
            decrease_role = None
            if increase_id:
                result = await session.execute(select(UserModel.role).where(UserModel.id == increase_id))
                increase_role = result.scalar_one_or_none()
            if decrease_id:
                result = await session.execute(select(UserModel.role).where(UserModel.id == decrease_id))
                decrease_role = result.scalar_one_or_none()
            fee_column = f"{direction}_fee"
            if increase_role == Role.MERCHANT and decrease_role == Role.AGENT:
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.merchant_id == increase_id,
                        FeeContractModel.user_id == decrease_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                dec_contracts = result.scalars().all()
                team_ids = [c.team_id for c in dec_contracts]
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.merchant_id == increase_id,
                        FeeContractModel.user_id == increase_id,
                        FeeContractModel.team_id.in_(team_ids),
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                inc_contracts = result.scalars().all()

                inc_by_team_and_tag = {(c.team_id, c.tag_id): c for c in inc_contracts}
                dec_by_team_and_tag = {(c.team_id, c.tag_id): c for c in dec_contracts}

                team_tag_pairs = set(inc_by_team_and_tag) & set(dec_by_team_and_tag)

                for team_id, tag in team_tag_pairs:
                    inc = inc_by_team_and_tag[(team_id, tag)]
                    dec = dec_by_team_and_tag[(team_id, tag)]

                    dec_value = getattr(dec, fee_column)
                    if dec_value < delta:
                        raise exceptions.FeeWillBeNegative()

                    setattr(inc, fee_column, getattr(inc, fee_column) + delta)
                    setattr(dec, fee_column, dec_value - delta)

                validate_fee_total(session, list(inc_by_team_and_tag.values()) + list(dec_by_team_and_tag.values()), fee_column)
            elif increase_role == Role.AGENT and decrease_role == Role.MERCHANT:
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.user_id == increase_id,
                        FeeContractModel.merchant_id == decrease_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                inc_contracts = result.scalars().all()

                team_ids = [c.team_id for c in inc_contracts]

                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.merchant_id == decrease_id,
                        FeeContractModel.user_id == decrease_id,
                        FeeContractModel.team_id.in_(team_ids),
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                dec_contracts = result.scalars().all()

                inc_by_team_and_tag = {(c.team_id, c.tag_id): c for c in inc_contracts}
                dec_by_team_and_tag = {(c.team_id, c.tag_id): c for c in dec_contracts}

                for key in set(inc_by_team_and_tag) & set(dec_by_team_and_tag):
                    inc = inc_by_team_and_tag[key]
                    dec = dec_by_team_and_tag[key]

                    dec_value = getattr(dec, fee_column)
                    if dec_value < delta:
                        raise exceptions.FeeWillBeNegative()

                    setattr(inc, fee_column, getattr(inc, fee_column) + delta)
                    setattr(dec, fee_column, dec_value - delta)

                validate_fee_total(session, list(inc_by_team_and_tag.values()) + list(dec_by_team_and_tag.values()), fee_column)
            elif decrease_role is None and increase_role == Role.AGENT:
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.user_id == increase_id,
                        FeeContractModel.merchant_id == merchant_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                agent_contracts = result.scalars().all()
                team_ids = list({c.team_id for c in agent_contracts})
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.team_id.in_(team_ids),
                        FeeContractModel.merchant_id == merchant_id,
                        FeeContractModel.user_id == FeeContractModel.team_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                team_contracts = result.scalars().all()
                team_contracts_by_team_merchant_tag = defaultdict(list)
                for c in team_contracts:
                    team_contracts_by_team_merchant_tag[(c.team_id, c.merchant_id, c.tag_id)].append(c)
                for agent_contract in agent_contracts:
                    team_id = agent_contract.team_id
                    merchant_ids = agent_contract.merchant_id
                    tag = agent_contract.tag_id
                    key = (team_id, merchant_ids, tag)
                    team_entries = team_contracts_by_team_merchant_tag.get(key, [])
                    inc_value = getattr(agent_contract, fee_column)
                    setattr(agent_contract, fee_column, inc_value + delta)
                    for team_contract in team_entries:
                        current = getattr(team_contract, fee_column)
                        if current < delta:
                            raise exceptions.FeeWillBeNegative()
                        setattr(team_contract, fee_column, current - delta)
                        break
                validate_fee_total(session, agent_contracts + team_contracts, fee_column)
            elif increase_role is None and decrease_role == Role.MERCHANT:
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.merchant_id == decrease_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                contracts = result.scalars().all()

                merchant_contracts = [c for c in contracts if c.user_id == decrease_id]
                team_contracts = {(c.team_id, c.tag_id): c for c in contracts if c.user_id == c.team_id}

                for mc in merchant_contracts:
                    key = (mc.team_id, mc.tag_id)
                    team = team_contracts.get(key)

                    if getattr(mc, fee_column) < delta:
                        raise exceptions.FeeWillBeNegative()

                    setattr(mc, fee_column, getattr(mc, fee_column) - delta)
                    setattr(team, fee_column, getattr(team, fee_column) + delta)
                validate_fee_total(session, merchant_contracts + list(team_contracts.values()), fee_column)
            elif decrease_role == Role.AGENT and increase_role is None:
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.user_id == decrease_id,
                        FeeContractModel.merchant_id == merchant_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                agent_contracts = result.scalars().all()
                team_ids = list({c.team_id for c in agent_contracts})
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.team_id.in_(team_ids),
                        FeeContractModel.user_id == FeeContractModel.team_id,
                        FeeContractModel.merchant_id == merchant_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                team_contracts = result.scalars().all()
                team_contracts_by_team_merchant_tag = defaultdict(list)
                for c in team_contracts:
                    team_contracts_by_team_merchant_tag[(c.team_id, c.merchant_id, c.tag_id)].append(c)
                for agent_contract in agent_contracts:
                    team_id = agent_contract.team_id
                    merchant_ids = agent_contract.merchant_id
                    tag = agent_contract.tag_id
                    key = (team_id, merchant_ids, tag)
                    team_entries = team_contracts_by_team_merchant_tag.get(key, [])
                    dec_value = getattr(agent_contract, fee_column)
                    if dec_value < delta:
                        raise exceptions.FeeWillBeNegative()
                    setattr(agent_contract, fee_column, dec_value - delta)
                    for team_contract in team_entries:
                        setattr(team_contract, fee_column, getattr(team_contract, fee_column) + delta)
                        break
                all_team_contracts = sum(team_contracts_by_team_merchant_tag.values(), [])
                validate_fee_total(session, agent_contracts + all_team_contracts, fee_column)
            elif increase_role == Role.MERCHANT and decrease_role is None:
                result = await session.execute(
                    select(FeeContractModel)
                    .where(
                        FeeContractModel.merchant_id == increase_id,
                        FeeContractModel.is_deleted == False,
                        *([FeeContractModel.tag_id == tag_id] if tag_id else [])
                    )
                    .with_for_update()
                )
                contracts = result.scalars().all()

                merchant_contracts = [c for c in contracts if c.user_id == increase_id]
                team_contracts = {(c.team_id, c.tag_id): c for c in contracts if c.user_id == c.team_id}

                for mc in merchant_contracts:
                    key = (mc.team_id, mc.tag_id)
                    team = team_contracts.get(key)
                    team_value = getattr(team, fee_column)
                    if team_value < delta:
                        raise exceptions.FeeWillBeNegative()

                    setattr(mc, fee_column, getattr(mc, fee_column) + delta)
                    setattr(team, fee_column, team_value - delta)
                validate_fee_total(session, merchant_contracts + list(team_contracts.values()), fee_column)
            else:
                raise Exception("Incorrect role combination")

