from fastapi import status
from fastapi.exceptions import HTTPException
from datetime import datetime
from typing import List

from sqlalchemy import and_, case, select, false, true, func

from app.core.constants import Status
from app.core.session import async_session, ro_async_session
from app.models import TrafficWeightContractModel, UserModel, ExternalTransactionModel, BankDetailModel, \
    UserBalanceChangeNonceModel, MerchantModel, TeamModel
from app.schemas.admin.TrafficWeightScheme import TrafficWeightScheme
from app.utils.decorators import raise_if_none
from app.functions.analytics import get_450errors_count


class TrafficWeightRepo:
    @classmethod
    async def list_for_stats(cls,
                             merchant_id: str,
                             type: str,
                             date_from: datetime,
                             bank: str | None = None,
                             payment_system: str | None = None,
                             is_vip: str | None = None
                             ):
        _, teams_stats = await cls.list(merchant_id, type, date_from, bank, payment_system, is_vip)
        total_transactions = 0
        accepted_transactions = 0
        no_pending_transactions = 0
        total_type_count = 0
        total_teams = 0
        for team in teams_stats:
            if team.stats[
                "is_enabled"] and team.inbound_traffic_weight > 0 and team.trust_balance > team.credit_factor and \
                    team.stats["count_type"] != 0:
                total_teams += 1
                total_type_count += team.stats["count_type"]
            total_transactions += team.stats["all_period"]
            no_pending_transactions += team.stats["no_pending_period"]
            accepted_transactions += team.stats["accept_period"]
        count_errors = await get_450errors_count(merchant_id, type, date_from, datetime.utcnow(), bank, payment_system, is_vip)
        return total_teams, total_type_count, total_transactions, accepted_transactions, no_pending_transactions, count_errors

    @classmethod
    async def merchant_stats(cls,
                             merchant_id: str,
                             type: str,
                             date_from: datetime,
                             bank: str | None = None,
                             payment_system: str | None = None,
                             is_vip: str | None = None
                             ):
        async with ro_async_session() as session:
            total_teams, total_type_count, total_transactions, accepted_transactions, no_pending_transactions, count_errors = await cls.list_for_stats(
                merchant_id, type, date_from, bank, payment_system, is_vip)
            details_issuance = float(total_transactions * 100 / (
                    total_transactions + count_errors)) if total_transactions + count_errors > 0 else 0.0
            if is_vip == "true":
                is_vip_bool = True
            elif is_vip == "false":
                is_vip_bool = False
            else:
                is_vip_bool = None
            combined_query = (
                select(
                    MerchantModel.credit_factor,
                    func.count(
                        case(
                            (
                                and_(
                                    ExternalTransactionModel.direction == 'inbound',
                                    ExternalTransactionModel.status == Status.PENDING,
                                    ExternalTransactionModel.bank_detail_bank == bank if bank else true(),
                                    BankDetailModel.payment_system == payment_system if payment_system else true(),
                                    BankDetailModel.is_vip == is_vip_bool if is_vip is not None else true()
                                ),
                                1
                            )
                        )
                    ).label("pending_in"),
                    func.count(
                        case(
                            (
                                and_(
                                    ExternalTransactionModel.direction == 'outbound',
                                    ExternalTransactionModel.status == Status.PENDING,
                                    ExternalTransactionModel.bank_detail_bank == bank if bank else true()
                                ),
                                1
                            )
                        )
                    ).label("pending_out"),
                    UserBalanceChangeNonceModel.trust_balance,
                    UserBalanceChangeNonceModel.locked_balance
                )
                .join(
                    UserBalanceChangeNonceModel,
                    UserBalanceChangeNonceModel.balance_id == MerchantModel.balance_id
                )
                .outerjoin(
                    ExternalTransactionModel,
                    and_(
                        ExternalTransactionModel.merchant_id == merchant_id,
                        ExternalTransactionModel.type == type,
                        ExternalTransactionModel.status == Status.PENDING
                    )
                )
                .outerjoin(
                    BankDetailModel,
                    ExternalTransactionModel.bank_detail_id == BankDetailModel.id
                )
                .where(MerchantModel.id == merchant_id)
                .group_by(
                    MerchantModel.balance_id, MerchantModel.credit_factor,
                    UserBalanceChangeNonceModel.trust_balance, UserBalanceChangeNonceModel.locked_balance
                )
            )

            result = await session.execute(combined_query)
            data = result.fetchone()

            if data:
                credit_factor = data.credit_factor
                trust_balance = data.trust_balance
                locked_balance = data.locked_balance
                pending_inbound = data.pending_in or 0
                pending_outbound = data.pending_out or 0
            else:
                credit_factor = 0
                trust_balance = 0
                locked_balance = 0
                pending_inbound = 0
                pending_outbound = 0

            conversion_rate = float(
                accepted_transactions * 100.0 / no_pending_transactions) if no_pending_transactions > 0 else 0.0

            merchant_stats = {
                "conversion_rate": conversion_rate,
                "accepted_transactions": accepted_transactions,
                "total_transactions": total_transactions,
                "no_pending_transactions": no_pending_transactions,
                "count_type": total_type_count,
                "total_teams": total_teams,
                "details_issuance": details_issuance,
                "total_transactions_with_errors": total_transactions + count_errors,
                "pending_inbound": pending_inbound,
                "pending_outbound": pending_outbound,
                "trust_balance": trust_balance // 1000000,
                "locked_balance": locked_balance // 1000000,
                "credit_factor": credit_factor,
            }
            return merchant_stats

    @classmethod
    async def list(cls,
                   merchant_id: str,
                   type: str,
                   date_from: datetime,
                   bank: str | None = None,
                   payment_system: str | None = None,
                   is_vip: str | None = None
                   ) -> [List[str], List[TrafficWeightScheme]]:
        async with ro_async_session() as session:
            if is_vip == "true":
                is_vip_bool = True
            elif is_vip == "false":
                is_vip_bool = False
            else:
                is_vip_bool = None
            result = await session.execute(
                select(
                    TrafficWeightContractModel.id.label("id"),
                    TrafficWeightContractModel.team_id,
                    TrafficWeightContractModel.inbound_traffic_weight,
                    TrafficWeightContractModel.type,
                    TeamModel.name.label('team_name'),
                    (
                        case(
                            (
                                TrafficWeightContractModel.outbound_traffic_weight > 0,
                                True,
                            ),
                            else_=False,
                        ).label("is_outbound_traffic")
                    ),
                    TrafficWeightContractModel.create_timestamp.label(
                        "create_timestamp"
                    ),
                    TeamModel.is_inbound_enabled,
                    TeamModel.credit_factor,
                    TeamModel.balance_id,
                    UserBalanceChangeNonceModel.trust_balance,
                    UserBalanceChangeNonceModel.locked_balance,
                    TrafficWeightContractModel.outbound_amount_less_or_eq,
                    TrafficWeightContractModel.outbound_amount_great_or_eq,
                    TrafficWeightContractModel.outbound_bank_in,
                    TrafficWeightContractModel.outbound_bank_not_in
                ).join(TeamModel, TeamModel.id == TrafficWeightContractModel.team_id).where(
                    and_(
                        TrafficWeightContractModel.merchant_id == merchant_id,
                        TrafficWeightContractModel.is_deleted == false(),
                        TeamModel.is_blocked == false()
                    ),
                ).join(UserBalanceChangeNonceModel,
                       UserBalanceChangeNonceModel.balance_id == UserModel.balance_id, isouter=True).where(
                    and_(
                        TrafficWeightContractModel.merchant_id == merchant_id,
                        TrafficWeightContractModel.is_deleted == false(),
                        MerchantModel.is_blocked == false()
                    ),
                ).filter(TrafficWeightContractModel.type == type)
            )
            fee_contracts = result.all()
            conv_period_subquery = select(
                TeamModel.id.label("team_id"),
                func.count(case((ExternalTransactionModel.status == 'accept', 1))).label("count_accept_period"),
                func.count(ExternalTransactionModel.id).label("count_all_period"),
                func.count(case((ExternalTransactionModel.status != 'pending', 1))).label("count_no_pending_period"),
            ).join(ExternalTransactionModel, ExternalTransactionModel.team_id == UserModel.id).where(
                and_(
                    ExternalTransactionModel.type == type,
                    ExternalTransactionModel.direction == "inbound",
                    ExternalTransactionModel.merchant_id == merchant_id,
                    ExternalTransactionModel.create_timestamp >= date_from,
                    MerchantModel.is_blocked == false()
                )
            ).join(BankDetailModel, BankDetailModel.id == ExternalTransactionModel.bank_detail_id).where(
                and_(
                    BankDetailModel.bank == bank if bank else true(),
                    BankDetailModel.payment_system == payment_system if payment_system else true(),
                    BankDetailModel.is_vip == is_vip_bool if is_vip is not None else true()
                )

            ).group_by(TeamModel.id).subquery()

            conv_period_result = await session.execute(
                select(
                    conv_period_subquery.c.team_id,
                    conv_period_subquery.c.count_accept_period,
                    conv_period_subquery.c.count_all_period,
                    conv_period_subquery.c.count_no_pending_period
                )
            )
            conv_period_stats = {row.team_id: row for row in conv_period_result}
            count_type_result = await session.execute(
                select(
                    TeamModel.id.label("team_id"),
                    *[func.sum(case((and_(BankDetailModel.type == type, BankDetailModel.bank == bank if bank else true(),
                                          BankDetailModel.payment_system == payment_system if payment_system else true(),
                                          BankDetailModel.is_vip == is_vip_bool if is_vip is not None else true()), 1), else_=0)).label(f"{type}")],
                ).join(TeamModel, TeamModel.id == BankDetailModel.team_id).where(
                    and_(
                        BankDetailModel.is_active == true(),
                        BankDetailModel.is_deleted == false(),
                        TeamModel.is_blocked == false(),
                        TeamModel.id.in_(
                            select(TrafficWeightContractModel.team_id).where(
                                and_(
                                    TrafficWeightContractModel.merchant_id == merchant_id,
                                    TrafficWeightContractModel.is_deleted == false()
                                )
                            )
                        )
                    )
                ).group_by(TeamModel.id)
            )
            count_types_stats = {
                row.team_id: {"count_type": row[1]} for row in count_type_result
            }
            res = [[type], [
                TrafficWeightScheme(
                    id=contract.id,
                    team_id=contract.team_id,
                    merchant_id=merchant_id,
                    type=contract.type,
                    inbound_traffic_weight=contract.inbound_traffic_weight,
                    is_outbound_traffic=contract.is_outbound_traffic,
                    outbound_amount_less_or_eq=contract.outbound_amount_less_or_eq,
                    outbound_amount_great_or_eq=contract.outbound_amount_great_or_eq,
                    outbound_bank_in=[
                        s for s in contract.outbound_bank_in.strip('#').split('#')
                    ] if contract.outbound_bank_in else [],

                    outbound_bank_not_in=[
                        s for s in contract.outbound_bank_not_in.strip('#').split('#')
                    ] if contract.outbound_bank_not_in else [],
                    create_timestamp=contract.create_timestamp,
                    team_name=contract.team_name,
                    trust_balance=contract.trust_balance // 1000000 if contract.trust_balance else 0,
                    locked_balance=contract.locked_balance // 1000000 if contract.locked_balance else 0,
                    credit_factor=contract.credit_factor,
                    stats={
                        "conv_period": float(
                            conv_period_stats.get(contract.team_id).count_accept_period / conv_period_stats.get(
                                contract.team_id).count_no_pending_period * 100.0) if conv_period_stats.get(
                            contract.team_id) and conv_period_stats.get(contract.team_id).count_no_pending_period > 0 else 0.0,
                        "count_type": count_types_stats.get(contract.team_id)["count_type"] if count_types_stats.get(
                            contract.team_id) else 0,
                        "accept_period": conv_period_stats.get(
                            contract.team_id).count_accept_period if conv_period_stats.get(
                            contract.team_id) else 0,
                        "all_period": conv_period_stats.get(contract.team_id).count_all_period if conv_period_stats.get(
                            contract.team_id) else 0,
                        "no_pending_period": conv_period_stats.get(contract.team_id).count_no_pending_period if conv_period_stats.get(
                            contract.team_id) else 0,
                        "is_enabled": contract.is_inbound_enabled or False,
                    }
                )
                for contract in fee_contracts
            ]]
            res[1].sort(
                key=lambda x: (
                    -x.inbound_traffic_weight,
                    -int(x.is_outbound_traffic),
                    -int(x.stats['is_enabled']),
                    -x.stats['all_period'],
                    x.team_name
                )
            )
            return res

    @classmethod
    async def create(
            cls, is_outbound_traffic: bool, comment: str = "", team_id: str = None,
            merchant_id: str = None, **kwargs
    ) -> TrafficWeightScheme:
        async with async_session() as session:
            currency_id = (await session.execute(
                select(MerchantModel.currency_id)
                .where(MerchantModel.id == merchant_id)
            )).scalar_one_or_none()

            traffic_weight = TrafficWeightContractModel(
                team_id=team_id,
                currency_id=currency_id,
                comment=comment,
                outbound_traffic_weight=1 if is_outbound_traffic else 0,
                is_deleted=False,
                merchant_id=merchant_id,
                **kwargs,
            )
            session.add(traffic_weight)
            await session.commit()
            await session.refresh(traffic_weight)

            team_result = (await session.execute(
                select(TeamModel.name, TeamModel.credit_factor)
                .where(TeamModel.id == team_id)
            )).first()

            if team_result:
                team_name, credit_factor = team_result
            
            locked_balance = (await session.execute(select(UserBalanceChangeNonceModel.locked_balance).filter(
                UserBalanceChangeNonceModel.balance_id == team_id))).scalar() or 0

            trust_balance = (await session.execute(select(UserBalanceChangeNonceModel.trust_balance).filter(
                UserBalanceChangeNonceModel.balance_id == team_id))).scalar() or 0

            return TrafficWeightScheme(
                id=traffic_weight.id,
                merchant_id=traffic_weight.merchant_id,
                team_id=traffic_weight.team_id,
                type=traffic_weight.type,
                credit_factor=credit_factor,
                locked_balance=locked_balance,
                trust_balance=trust_balance,
                inbound_traffic_weight=traffic_weight.inbound_traffic_weight,
                is_outbound_traffic=bool(traffic_weight.outbound_traffic_weight),
                create_timestamp=traffic_weight.create_timestamp,
                outbound_bank_in=[],
                outbound_bank_not_in=[],
                stats={
                    "conv_period": 0.0,
                    "count_type": 0,
                    "accept_period": 0,
                    "all_period": 0,
                    "no_pending_period": 0,
                    "is_enabled": False,
                },
                team_name=team_name
            )

    @classmethod
    @raise_if_none(LookupError)
    async def update(cls, id: str, **kwargs) -> TrafficWeightScheme | None:
        async with async_session() as session:
            result = await session.execute(
                select(TrafficWeightContractModel).where(
                    TrafficWeightContractModel.id == id
                )
            )
            traffic_weight = result.scalar_one()
            if not traffic_weight:
                return
            for field, value in kwargs.items():
                if value is not None:
                    if field == 'is_outbound_traffic':
                        print('bur')
                        traffic_weight.outbound_traffic_weight = value
                    elif field == 'outbound_bank_in':
                        traffic_weight.outbound_bank_in = None if not value else '#' + '#'.join(value) + '#'
                    elif field == 'outbound_bank_not_in':
                        traffic_weight.outbound_bank_not_in = None if not value else '#' + '#'.join(value) + '#'
                    else:
                        setattr(traffic_weight, field, value)
                elif field == "outbound_amount_less_or_eq":
                    traffic_weight.outbound_amount_less_or_eq = value
                elif field == "outbound_amount_great_or_eq":
                    traffic_weight.outbound_amount_great_or_eq = value
            await session.commit()
            await session.refresh(traffic_weight)
            
            
            team_result = (await session.execute(
                select(TeamModel.name, TeamModel.credit_factor)
                .where(TeamModel.id == traffic_weight.team_id)
            )).first()

            if team_result:
                team_name, credit_factor = team_result

            locked_balance = (await session.execute(select(UserBalanceChangeNonceModel.locked_balance).filter(
                UserBalanceChangeNonceModel.balance_id == traffic_weight.team_id))).scalar() or 0
            trust_balance = (await session.execute(select(UserBalanceChangeNonceModel.trust_balance).filter(
                UserBalanceChangeNonceModel.balance_id == traffic_weight.team_id))).scalar() or 0

            print(traffic_weight.outbound_traffic_weight)

            return TrafficWeightScheme(
                id=traffic_weight.id,
                merchant_id=traffic_weight.merchant_id,
                team_id=traffic_weight.team_id,
                type=traffic_weight.type,
                credit_factor=credit_factor,
                locked_balance=locked_balance,
                trust_balance=trust_balance,
                inbound_traffic_weight=traffic_weight.inbound_traffic_weight,
                is_outbound_traffic=bool(traffic_weight.outbound_traffic_weight),
                outbound_amount_less_or_eq=traffic_weight.outbound_amount_less_or_eq,
                outbound_amount_great_or_eq=traffic_weight.outbound_amount_great_or_eq,
                outbound_bank_in=(
                    traffic_weight.outbound_bank_in.strip('#').split('#')
                    if traffic_weight.outbound_bank_in else []
                ),
                outbound_bank_not_in=(
                    traffic_weight.outbound_bank_not_in.strip('#').split('#')
                    if traffic_weight.outbound_bank_not_in else []
                ),
                create_timestamp=traffic_weight.create_timestamp,
                stats={
                    "conv_period": 0.0,
                    "count_type": 0,
                    "accept_period": 0,
                    "all_period": 0,
                    "is_enabled": False,
                    "no_pending_period": 0
                },
                team_name=team_name
            )

    @classmethod
    @raise_if_none(LookupError)
    async def delete(cls, id: str) -> TrafficWeightScheme | None:
        async with async_session() as session:
            result = await session.execute(
                select(TrafficWeightContractModel).where(
                    TrafficWeightContractModel.id == id
                )
            )

            traffic_weight = result.scalar_one_or_none()

            if traffic_weight is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="id not found"
                )

            await session.delete(traffic_weight)
            await session.commit()
            
            team_result = (await session.execute(
                select(TeamModel.name, TeamModel.credit_factor)
                .where(TeamModel.id == traffic_weight.team_id)
            )).first()

            if team_result:
                team_name, credit_factor = team_result

            locked_balance = (await session.execute(select(UserBalanceChangeNonceModel.locked_balance).filter(
                UserBalanceChangeNonceModel.balance_id == traffic_weight.team_id))).scalar() or 0

            trust_balance = (await session.execute(select(UserBalanceChangeNonceModel.trust_balance).filter(
                UserBalanceChangeNonceModel.balance_id == traffic_weight.team_id))).scalar() or 0
                
            return TrafficWeightScheme(
                id=traffic_weight.id,
                merchant_id=traffic_weight.merchant_id,
                team_id=traffic_weight.team_id,
                type=traffic_weight.type,
                credit_factor=credit_factor,
                locked_balance=locked_balance,
                trust_balance=trust_balance,
                inbound_traffic_weight=traffic_weight.inbound_traffic_weight,
                is_outbound_traffic=bool(traffic_weight.outbound_traffic_weight),
                create_timestamp=traffic_weight.create_timestamp,
                outbound_bank_in=[],
                outbound_bank_not_in=[],
                stats={
                    "conv_period": 0.0,
                    "count_type": 0,
                    "accept_period": 0,
                    "all_period": 0,
                    "is_enabled": False,
                    "no_pending_period": 0
                },
                team_name=team_name
            )
