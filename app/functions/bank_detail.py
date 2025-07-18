import uuid
from sqlalchemy import select, false, or_, true, func, literal, delete, text, update, case, and_

#from app.worker.celery import regenerate_details_daily_task
from app import exceptions
from app.core.constants import Type, DECIMALS
import logging
from app.core.session import async_session, ro_async_session
from app.models.BankDetailModel import BankDetailModel
from app.models.VipPayerModel import VipPayerModel
from app.models.UserModel import UserModel
from app.models.ExternalTransactionModel import ExternalTransactionModel
from app.models.UserBalanceChangeModel import UserBalanceChangeModel
from app.schemas.BankDetailScheme import *
from app.schemas.LogsSchema import *
from datetime import datetime
from app.services.notification_service import send_notification
from app.schemas.NotificationsSchema import EnableReqForFillSupportNotificationSchema, DisableReqForFillSupportNotificationSchema, ReqDisabledNotificationDataSchema
import hashlib

logger = logging.getLogger(__name__)


async def time_to_minutes(t: datetime.time) -> int:
    return t.hour * 60 + t.minute

# -------------------------------------------------CREATE------------------------------------------
async def get_number_of_bank_details(number: str,
                                     bank: str,
                                     type: str,
                                     second_number: str | None,
                                     session: async_session):
    bank_details_q = await session.execute(
        select(BankDetailModel.id).select_from(BankDetailModel).filter(
            BankDetailModel.number == number,
            BankDetailModel.second_number == second_number if second_number is not None else True,
            BankDetailModel.bank == bank,
            BankDetailModel.type == type,
            BankDetailModel.is_deleted != true()
        ).limit(2)
    )
    counter = 0
    for _ in bank_details_q.all():
        counter += 1
    return counter


async def create_bank_detail(
        bank_detail_scheme_request_create_db: BankDetailSchemeRequestCreateDB
) -> BankDetailSchemeResponse:
    async with async_session() as session:
        number_same_bd = await get_number_of_bank_details(bank_detail_scheme_request_create_db.number,
                                                          bank_detail_scheme_request_create_db.bank,
                                                          bank_detail_scheme_request_create_db.type,
                                                          bank_detail_scheme_request_create_db.second_number,
                                                          session)
        if number_same_bd > 0:
            raise exceptions.BankDetailDuplicateException()
        #if bank_detail_scheme_request_create_db.transactions_count_limit and sum(item[2] for item in bank_detail_scheme_request_create_db.transactions_count_limit) > 1000:
        #    raise exceptions.BankDetailTransactionLimitExceeded()
        data = bank_detail_scheme_request_create_db.__dict__.copy()
        data.pop("period_time", None)
        bank_detail_model: BankDetailModel = BankDetailModel(
            **data,
            amount_used=0,
            is_deleted=False,
            is_auto_active=False
        )
        if bank_detail_model is None:
            raise exceptions.BankDetailNotFoundException()
        
        if bank_detail_model.type in (Type.CARD, Type.ACCOUNT):
            if bank_detail_model.bank != 'alfabusiness':
                bank_detail_model.comment = bank_detail_model.number[-4:] if bank_detail_model.number and len(
                    bank_detail_model.number) >= 4 else None
        
        session.add(bank_detail_model)
        await session.commit()

        print("HERE")

        if bank_detail_scheme_request_create_db.profile_id is None:
            bank_detail_model.profile_id = bank_detail_model.id

        profile_id = bank_detail_model.profile_id

        stmt = text("""
            SELECT COUNT(*) 
            FROM vip_payer_model
            WHERE bank_detail_id = :profile_id
        """)
        result = await session.execute(stmt, {"profile_id": profile_id})
        vip_count = result.scalar_one()

        bank_detail_model.count_vip_payers = vip_count

        if bank_detail_model.is_vip is True:
            stmt = text("""
                UPDATE bank_detail_model
                SET max_vip_payers = :new_max
                WHERE profile_id = :profile_id AND is_deleted = FALSE
            """)
            await session.execute(stmt, {
                "new_max": bank_detail_model.max_vip_payers,
                "profile_id": profile_id
            })
            await session.commit()
        elif bank_detail_model.is_vip is False:
            stmt = text("""
                SELECT max_vip_payers
                FROM bank_detail_model
                WHERE profile_id = :profile_id AND is_deleted = FALSE
                LIMIT 1
            """)
            result = await session.execute(stmt, {"profile_id": profile_id})
            max_vip_value = result.scalar_one_or_none()

            if max_vip_value is not None:
                update_stmt = (
                    update(BankDetailModel)
                    .where(BankDetailModel.id == bank_detail_model.id)
                    .values(max_vip_payers=max_vip_value)
                )
                await session.execute(update_stmt)
                await session.commit()

        #if bank_detail_model.auto_managed is True and bank_detail_model.transactions_count_limit is not None:
        #    regenerate_details_daily_task(bank_detail_model.id,
        #                                  bank_detail_model.transactions_count_limit,
        #                                  min(bank_detail_model.is_active, bank_detail_model.is_deleted == False))
        await session.commit()
        return BankDetailSchemeResponse(
            **bank_detail_model.__dict__,
            period_time=[
                await time_to_minutes(bank_detail_model.period_start_time),
                await time_to_minutes(bank_detail_model.period_finish_time)
            ] if bank_detail_model.period_start_time and bank_detail_model.period_finish_time else None
        )


# -------------------------------------------------LIST--------------------------------------------
async def get_bank_detail(id: str):
    async with async_session() as session:
        bank_detail_req = await session.execute(
            select(BankDetailModel)
            .filter(BankDetailModel.id == id)
        )
        bank_detail_model = bank_detail_req.scalars().first()
        result = BankDetailSchemeResponse(
            **bank_detail_model.__dict__,
            period_time=[
                await time_to_minutes(bank_detail_model.period_start_time),
                await time_to_minutes(bank_detail_model.period_finish_time)
            ] if bank_detail_model.period_start_time and bank_detail_model.period_finish_time else None
        )
        return result

def get_search_filters(request: BankDetailSchemeRequestListDB):
    search_without_plus = (request.search or "").replace("+", "")
    model = BankDetailModel
    queries_none = [
        model.bank == request.bank if request.bank is not None else None,
        model.payment_system == request.payment_system if request.payment_system is not None else None,
        model.is_vip == request.is_vip if request.is_vip is not None else None,
        model.is_active == request.is_active if request.is_active is not None else None,
        or_(
            func.replace(model.number, "+", "") == search_without_plus,
            model.id == request.search,
            model.name.icontains(request.search),
            model.device_hash.icontains(request.search),
            model.second_number == request.search
        ) if request.search is not None else None
    ]
    queries = []
    for query in queries_none:
        if query is not None:
            queries.append(query)
    
    return queries


async def list_bank_detail(
        bank_detail_scheme_request_list_db: BankDetailSchemeRequestListDB
) -> BankDetailSchemeResponseList:
    async with ro_async_session() as session:
        queries = get_search_filters(request=bank_detail_scheme_request_list_db)
        bank_detail_list = await session.execute(
            select(BankDetailModel).filter(
                BankDetailModel.team_id == bank_detail_scheme_request_list_db.team_id,
                BankDetailModel.offset_id < bank_detail_scheme_request_list_db.last_offset_id,
                BankDetailModel.is_deleted == false()).filter(
                *queries
            )
            .order_by(
                BankDetailModel.offset_id.desc())
            .limit(bank_detail_scheme_request_list_db.limit))
        result = BankDetailSchemeResponseList(
            items=[
                {
                    **i.__dict__,
                    "today_amount_used": 0 if i.last_transaction_timestamp.date() < datetime.utcnow().date() else i.today_amount_used * DECIMALS,
                    "today_transactions_count": 0 if i.last_transaction_timestamp.date() < datetime.utcnow().date() else i.today_transactions_count,
                    "period_time": [
                        await time_to_minutes(i.period_start_time),
                        await time_to_minutes(i.period_finish_time)
                    ] if i.period_start_time and i.period_finish_time else None
                }
                for i in bank_detail_list.scalars().fetchall()
            ]
        )
        return result


async def list_profiles(team_id: str, bank: str | None = None, device_hash: str | None = None) -> BankDetailProfilesResponseList:
    async with ro_async_session() as session:
        bank_filter = true()
        device_hash_filter = true()

        if bank is not None:
            bank_filter = or_(
                BankDetailModel.bank == bank,
                BankDetailModel.bank.is_(None)
            )
        if device_hash is not None:
            device_hash_filter = or_(
                BankDetailModel.device_hash == device_hash,
                BankDetailModel.device_hash.is_(None)
            )

        conditions = []
        if bank is not None and device_hash is not None:
            conditions.append((
                (BankDetailModel.bank == bank) & (BankDetailModel.device_hash == device_hash),
                0
            ))
        if device_hash is not None:
            conditions.append((
                BankDetailModel.device_hash == device_hash,
                1
            ))
        if bank is not None:
            conditions.append((
                BankDetailModel.bank == bank,
                2
            ))

        priority_case = case(*conditions, else_=3)

        profile_list = await session.execute(
            select(BankDetailModel.profile_id, BankDetailModel.name).filter(
                BankDetailModel.team_id == team_id,
                BankDetailModel.is_deleted == false(),
                BankDetailModel.profile_id == BankDetailModel.id,
                BankDetailModel.is_vip == true(),
                bank_filter,
                device_hash_filter
            ).order_by(
                priority_case,
                BankDetailModel.offset_id.desc()
            )
        )

        result = BankDetailProfilesResponseList(
            items=[
                {
                    "profile_id": i[0],
                    "name": i[1]
                }
                for i in profile_list.all()
            ]
        )
        return result


async def get_statistic_detail(id: str, user_id: str) -> BankDetailStatisticSchemeResponse:
    async with ro_async_session() as session:
        day_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        profit_per_tx_subquery = (
            select(
                UserBalanceChangeModel.transaction_id.label("tx_id"),
                func.sum(UserBalanceChangeModel.fiat_profit_balance).label("profit")
            ).where(UserBalanceChangeModel.user_id == user_id)
            .group_by(UserBalanceChangeModel.transaction_id)
            .subquery()
        )

        main_q = (
            select(
                func.count(ExternalTransactionModel.id).label("total_transactions_count"),
                func.sum(case((ExternalTransactionModel.status == 'accept', 1), else_=0)).label(
                    "accept_transactions_count"),
                func.avg(case((ExternalTransactionModel.status == 'accept', ExternalTransactionModel.amount),
                              else_=None)).label("avg_amount"),
                func.sum(case((ExternalTransactionModel.status == 'accept', ExternalTransactionModel.amount),
                              else_=None)).label("sum_amount"),
                func.sum(case((ExternalTransactionModel.create_timestamp >= day_ago, 1), else_=0)).label(
                    "total_transactions_day"),
                func.sum(case((and_(ExternalTransactionModel.create_timestamp >= day_ago,
                                    ExternalTransactionModel.status == 'accept'), 1), else_=0)).label(
                    "accept_transactions_day"),
                func.avg(case((and_(ExternalTransactionModel.create_timestamp >= day_ago,
                                    ExternalTransactionModel.status == 'accept'),
                               ExternalTransactionModel.amount), else_=None)).label("avg_amount_day"),
                func.sum(case((and_(ExternalTransactionModel.create_timestamp >= day_ago,
                                    ExternalTransactionModel.status == 'accept'),
                               ExternalTransactionModel.amount), else_=None)).label("sum_amount_day"),
                func.avg(case((ExternalTransactionModel.status == 'accept', profit_per_tx_subquery.c.profit),
                              else_=None)).label("avg_profit"),
                func.sum(case((ExternalTransactionModel.status == 'accept', profit_per_tx_subquery.c.profit),
                              else_=None)).label("sum_profit"),
                func.avg(case((and_(ExternalTransactionModel.create_timestamp >= day_ago,
                                    ExternalTransactionModel.status == 'accept'),
                               profit_per_tx_subquery.c.profit), else_=None)).label("avg_profit_day"),
                func.sum(case((and_(ExternalTransactionModel.create_timestamp >= day_ago,
                                    ExternalTransactionModel.status == 'accept'),
                               profit_per_tx_subquery.c.profit), else_=None)).label("sum_profit_day")
            )
            .outerjoin(profit_per_tx_subquery, ExternalTransactionModel.id == profit_per_tx_subquery.c.tx_id)
            .where(ExternalTransactionModel.bank_detail_id == id).filter(ExternalTransactionModel.direction == 'inbound', ExternalTransactionModel.status != 'pending')
        )

        result = (await session.execute(main_q)).first()

        if result is None:
            return BankDetailStatisticSchemeResponse(
                id=id, count_transactions=0, count_transactions_day=0, average_amount=0,
                average_amount_day=0, average_profit=0, average_profit_day=0, sum_profit=0, sum_profit_day=0,
                conversion=None, conversion_day=None, average_fee=None, average_fee_day=None
            )

        total_transactions_count = result.total_transactions_count or 0
        accept_transactions_count = result.accept_transactions_count or 0
        avg_amount = int(result.avg_amount or 0)
        total_transactions_day = result.total_transactions_day or 0
        accept_transactions_day = result.accept_transactions_day or 0
        avg_amount_day = int(result.avg_amount_day or 0)
        avg_profit = int(result.avg_profit or 0)
        avg_profit_day = int(result.avg_profit_day or 0)
        sum_profit = int(result.sum_profit or 0)
        sum_profit_day = int(result.sum_profit_day or 0)
        sum_amount = int(result.sum_amount or 0)
        sum_amount_day = int(result.sum_amount_day or 0)

        conversion = int(
            (accept_transactions_count / total_transactions_count) * 100) if total_transactions_count > 0 else None
        conversion_day = int(
            (accept_transactions_day / total_transactions_day) * 100) if total_transactions_day > 0 else None

        average_fee = float(
            (sum_profit / sum_amount) * 100) if total_transactions_count > 0 else None
        average_fee_day = float(
            (sum_profit_day / sum_amount_day) * 100) if total_transactions_day > 0 else None

        return BankDetailStatisticSchemeResponse(
            id=id,
            count_transactions=accept_transactions_count,
            count_transactions_day=accept_transactions_day,
            average_amount=avg_amount,
            average_amount_day=avg_amount_day,
            average_profit=avg_profit,
            average_profit_day=avg_profit_day,
            sum_profit=sum_profit,
            sum_profit_day=sum_profit_day,
            conversion=conversion,
            conversion_day=conversion_day,
            average_fee=average_fee,
            average_fee_day=average_fee_day
        )


# -------------------------------------------------DELETE-------------------------------------------
async def delete_bank_detail(
        bank_detail_scheme_request_delete_db: BankDetailSchemeRequestDeleteDB
) -> BankDetailSchemeResponse:
    async with async_session() as session:
        bank_detail_req = await session.execute(
            select(BankDetailModel)
            .filter(
                BankDetailModel.team_id == bank_detail_scheme_request_delete_db.team_id)
            .filter(
                BankDetailModel.id == bank_detail_scheme_request_delete_db.id))
        bank_detail_model = bank_detail_req.scalars().first()
        if bank_detail_model is None:
            raise exceptions.BankDetailNotFoundException()
        bank_detail_model.is_deleted = True
        await session.execute(
            delete(VipPayerModel)
            .where(VipPayerModel.bank_detail_id == bank_detail_model.id)
        )

        await session.commit()
        
        result = BankDetailSchemeResponse(
            **bank_detail_model.__dict__,
            period_time=[
                await time_to_minutes(bank_detail_model.period_start_time),
                await time_to_minutes(bank_detail_model.period_finish_time)
            ] if bank_detail_model.period_start_time and bank_detail_model.period_finish_time else None
        )
        return result


# -------------------------------------------------UPDATE-------------------------------------------
def safe_dict(obj) -> dict:
    return {
        k: v for k, v in obj.__dict__.items()
        if not k.startswith("_sa_")
    }


async def update_bank_detail(
        bank_detail_scheme_request_update_db: BankDetailSchemeRequestUpdateDB
) -> BankDetailSchemeResponse:
    request_id = str(uuid.uuid4())
    async with (async_session() as session):
        bank_detail_req = await session.execute(
            select(BankDetailModel)
            .filter(
                BankDetailModel.team_id == bank_detail_scheme_request_update_db.team_id)
            .filter(
                BankDetailModel.id == bank_detail_scheme_request_update_db.id))
        
        bank_detail_model = bank_detail_req.scalars().first()
        if bank_detail_model is None:
            raise exceptions.BankDetailNotFoundException()
        if bank_detail_scheme_request_update_db.fiat_min_inbound is not None and bank_detail_scheme_request_update_db.is_active is not None:
            if bank_detail_scheme_request_update_db.fiat_min_inbound < 1000 and bank_detail_scheme_request_update_db.is_active == True and (bank_detail_model.is_active == False or bank_detail_model.fiat_min_inbound >= 1000):
                await send_notification(EnableReqForFillSupportNotificationSchema(
                    support_id="all",
                    data=ReqDisabledNotificationDataSchema(
                        number=bank_detail_scheme_request_update_db.number if bank_detail_scheme_request_update_db.number else bank_detail_model.number
                    )
                ))
        if ((bank_detail_scheme_request_update_db.fiat_min_inbound is not None and bank_detail_scheme_request_update_db.fiat_min_inbound >= 1000) or (bank_detail_scheme_request_update_db.is_active is not None and bank_detail_scheme_request_update_db.is_active == False)) and bank_detail_model.is_active == True and bank_detail_model.fiat_min_inbound < 1000:
            await send_notification(DisableReqForFillSupportNotificationSchema(
                support_id="all",
                data=ReqDisabledNotificationDataSchema(
                    number=bank_detail_scheme_request_update_db.number if bank_detail_scheme_request_update_db.number else bank_detail_model.number
                )
            ))
        name_q = await session.execute(
            select(UserModel.name).where(UserModel.id == bank_detail_scheme_request_update_db.team_id)
        )
        team_name = name_q.scalar()
        log_data = UpdateDetailLogSchema(
            request_id=request_id,
            team_name=team_name,
            team_id=bank_detail_scheme_request_update_db.team_id,
            id=bank_detail_scheme_request_update_db.id,
            was_is_vip=bank_detail_model.is_vip,
            new_is_vip=bank_detail_scheme_request_update_db.is_vip,
            was_is_active=bank_detail_model.is_active,
            new_is_active=bank_detail_scheme_request_update_db.is_active,
            fields_was=safe_dict(bank_detail_model),
            fields_new=bank_detail_scheme_request_update_db.model_dump()
        )

        logger.info(log_data.model_dump_json())
        logger.info(
            f"[UpdateDetail] - team_name = {team_name}, team_id = {bank_detail_scheme_request_update_db.team_id}, id = {bank_detail_scheme_request_update_db.id}, was is_vip = {bank_detail_model.is_vip}, new is_vip = {bank_detail_scheme_request_update_db.is_vip} = was is_active: {bank_detail_model.is_active} = new is_active: {bank_detail_scheme_request_update_db.is_active}, all fields was = {bank_detail_model.__dict__}, all fields new = {bank_detail_scheme_request_update_db.__dict__}"
        )
        if bank_detail_scheme_request_update_db.is_active is not None and bank_detail_scheme_request_update_db.is_active != bank_detail_model.is_active:
            bank_detail_model.need_check_automation = True
            bank_detail_model.update_timestamp = func.now()
        old_profile_id = bank_detail_model.profile_id
        rebind = bool(bank_detail_model.profile_id == bank_detail_model.id)
        bank_detail_model.update_if_not_none(
            bank_detail_scheme_request_update_db.__dict__
        )
        if old_profile_id != bank_detail_model.profile_id and rebind:
            update_stmt = (
                update(BankDetailModel)
                .where(BankDetailModel.profile_id == old_profile_id)
                .values(profile_id=bank_detail_model.profile_id)
            )
            await session.execute(update_stmt)
            delete_stmt = (
                delete(VipPayerModel).where(VipPayerModel.bank_detail_id == old_profile_id)
            )
            await session.execute(delete_stmt)
        await session.flush()
        if bank_detail_model.type in (Type.CARD, Type.ACCOUNT):
            if bank_detail_model.bank != 'alfabusiness':
                bank_detail_model.comment = bank_detail_model.number[-4:] if bank_detail_model.number and len(
                    bank_detail_model.number) >= 4 else None
        number_same_bd = await get_number_of_bank_details(bank_detail_model.number,
                                                          bank_detail_model.bank,
                                                          bank_detail_model.type,
                                                          bank_detail_model.second_number,
                                                          session)
        if number_same_bd > 1:
            raise exceptions.BankDetailDuplicateException()
        #if bank_detail_scheme_request_update_db.transactions_count_limit and sum(item[2] for item in bank_detail_scheme_request_update_db.transactions_count_limit) > 1000:
        #    raise exceptions.BankDetailTransactionLimitExceeded()
        profile_id = bank_detail_model.profile_id

        stmt = text("""
            SELECT COUNT(*) 
            FROM vip_payer_model
            WHERE bank_detail_id = :profile_id
        """)
        result = await session.execute(stmt, {"profile_id": profile_id})
        vip_count = result.scalar_one()

        update_stmt = (
            update(BankDetailModel)
            .where(BankDetailModel.profile_id == bank_detail_model.profile_id)
            .values(count_vip_payers=vip_count)
        )
        await session.execute(update_stmt)

        if bank_detail_model.is_vip is True:
            stmt = text("""
                UPDATE bank_detail_model
                SET max_vip_payers = :new_max
                WHERE profile_id = :profile_id AND is_deleted = FALSE
            """)
            await session.execute(stmt, {
                "new_max": bank_detail_model.max_vip_payers,
                "profile_id": profile_id
            })
        elif bank_detail_model.is_vip is False:
            stmt = text("""
                SELECT max_vip_payers
                FROM bank_detail_model
                WHERE profile_id = :profile_id AND is_deleted = FALSE
                LIMIT 1
            """)
            result = await session.execute(stmt, {"profile_id": profile_id})
            max_vip_value = result.scalar_one_or_none()

            if max_vip_value is not None:
                update_stmt = (
                    update(BankDetailModel)
                    .where(BankDetailModel.id == bank_detail_model.id)
                    .values(max_vip_payers=max_vip_value)
                )
                await session.execute(update_stmt)
        await session.commit()
        data = bank_detail_model.__dict__.copy()
        data.pop("today_amount_used", None)
        data.pop("today_transactions_count", None)
        data.pop("period_time", None)
        result = BankDetailSchemeResponse(
            today_amount_used=0 if bank_detail_model.last_transaction_timestamp.date() < datetime.utcnow().date() else bank_detail_model.today_amount_used * DECIMALS,
            today_transactions_count=0 if bank_detail_model.last_transaction_timestamp.date() < datetime.utcnow().date() else bank_detail_model.today_transactions_count,
            period_time=[
                await time_to_minutes(bank_detail_model.period_start_time),
                await time_to_minutes(bank_detail_model.period_finish_time)
            ] if bank_detail_model.period_start_time and bank_detail_model.period_finish_time else None,
            **data
        )
        #if bank_detail_scheme_request_update_db.auto_managed is True and bank_detail_scheme_request_update_db.transactions_count_limit is not None:
        #    regenerate_details_daily_task(bank_detail_model.id, bank_detail_scheme_request_update_db.transactions_count_limit, min(bank_detail_model.is_active, bank_detail_model.is_deleted == False))
        return result

# if __name__ == '__main__':
#     print(asyncio.run(get_number_of_bank_details('2202206903550577',
#                                                  'SBER',
#                                                  'card', '')))
# # print(asyncio.run(update_bank_detail(BankDetailSchemeRequestUpdateDB(
#     team_id='037ddaf2-1949-4e0e-b7a9-9e31f78f0451',
#     id='62bdbd4d-f983-4989-8ceb-7c29a43b4fe0',
#     bank='SBOL',
#     is_active=False,
#     type=None,
#     device_hash="HAHAHAHAHAHA",
#     comment="BURENIE",
#     number='2282282828228222',
#     amount_limit=100,
#     name=None,
#     currency=None
# ))))

# -------------------------------------------------TEST--------------------------------------------


# UPDATE
# print(asyncio.run(create_bank_detail(BankDetailSchemeRequestCreateDB(
#     team_id="037ddaf2-1949-4e0e-b7a9-9e31f78f0451",
#     name="First Card",
#     bank=Banks.SBER,
#     type=Types.MIR,
#     currency=Currencies.RUB,
#     number="220229828284628",
#     is_active=False,
#     amount_limit=0,
#     device_hash="dshfkjdshfjzDKJHFKDSJHKSJs",
#     comment="Для бабушки",
# ))))
# LIST
# print(asyncio.run(list_bank_detail(BankDetailSchemeRequestListDB(
#     last_offset_id=7,
#     limit=2,
#     team_id='037ddaf2-1949-4e0e-b7a9-9e31f78f0451'
# ))))
# DELETE
# print(asyncio.run(delete_bank_detail(BankDetailSchemeRequestDeleteDB(
#     team_id='037ddaf2-1949-4e0e-b7a9-9e31f78f0451',
#     id='62bdbd4d-f983-4989-8ceb-7c29a43b4fe0'
# ))))
# UPDATE

# TODO create filters like here
# async def update_bank_detail(
#         bank_detail_scheme_request_update_db: BankDetailSchemeRequestUpdateDB
# ) -> BankDetailSchemeRequestCreate:
#     filter_keys = []
#     for key, val in bank_detail_scheme_request_update_db.__dict__.items():
#         if val is not None:
#             filter_keys.append(key)
#     async with async_session() as session:
#         print(bank_detail_scheme_request_update_db.__getattribute__('team_id'))
#         bank_detail_req = await session.execute(
#             select(BankDetailModel)
#             .filter(
#                 BankDetailModel.team_id == bank_detail_scheme_request_update_db.team_id)
#             .filter(
#                 *[BankDetailModel.__getattribute__(BankDetailModel, i) ==
#                   bank_detail_scheme_request_update_db.__getattribute__(i)
#                   for i in filter_keys]))
#         bank_detail_model = bank_detail_req.scalars().one()
#         bank_detail_model.is_deleted = True
#         await session.commit()
#
#         return BankDetailSchemeResponseCreate(
#             **bank_detail_model.__dict__
#         )
