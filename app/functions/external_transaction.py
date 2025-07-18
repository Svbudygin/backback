import asyncio
import base64
import hashlib
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import random
import time
import uuid
import logging
import functools
from uuid import UUID
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from sqlalchemy.dialects import postgresql
from fastapi import UploadFile, Request, HTTPException, status as http_status
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
    literal, values
)
from sqlalchemy.sql import exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError

import app.api.telegram as tg
import app.exceptions as exceptions
import app.schemas.ExternalTransactionScheme as ETs
import app.schemas.InternalTransactionScheme as ITs
import app.schemas.v2.ExternalTransactionScheme as v2_ETs
from app.enums import TransactionFinalStatusEnum
from app.schemas.LogsSchema import *
import app.functions.binchecker as bcheck
from app.core import file_storage, redis
from app.core.constants import (
    ASSOCIATE_BANK,
    ASSOCIATE_MERCHANT_BANK,
    AUTO_CLOSE_EXTERNAL_TRANSACTIONS_S,
    BEFORE_CLOSE_OUT_EXTERNAL_TRANSACTIONS_S,
    DECIMALS,
    Direction,
    EconomicModel,
    Limit,
    Role,
    Status,
    Type,
    Banks,
    FUTURE_DATE,
    BANK_SCHEMAS,
    TEAM_OUTBOUND_CATEGORIES,
    SUPPORT_OUTBOUND_CATEGORIES,
    TRANSACTION_FINAL_STATUS_TITLES,
    USUAL_TYPES_INFO,
    REPLICATION_LAG_S
)
from app.core.session import async_session, ro_async_session
from app.functions import device
from app.functions.balance import (
    _get_currency,
    add_balance_changes,
    get_balance_id_by_user_id, get_balances,
)
from app.functions.change_tag_code_inbound import change_tag_code_inbound
from app.functions.device import preprocess_message
from app.functions.merchant_callback import merchant_callback
from app.functions.user import disable_user_by_credit_factor, get_credit_factor_, v2_user_get_by_id
from app.models import (
    CurrencyModel,
    InternalTransactionModel,
    MessageModel,
    TrafficWeightContractModel,
    UserBalanceChangeModel,
    UserModel,
    TagModel,
    GeoSettingsModel,
    MerchantModel,
    TeamModel,
    SupportModel,
    NamespaceModel,
    TelegramVerifierChatIdModel,
    VipPayerModel,
    UserBalanceChangeNonceModel,
    WhiteListPayerModel,
    TransferAssociationModel,
    AppealModel
)
from app.models.BankDetailModel import BankDetailModel
from app.models.ExternalTransactionModel import ExternalTransactionModel
from app.models.FeeContractModel import FeeContractModel
from app.schemas.admin.TagScheme import TagScheme
from app.schemas.WhitelistScheme import WhiteListPayerAddRequest
from app.schemas.UserScheme import (
    ExpandedUserSchemeResponse,
    UserIdNameResponse,
    UserTeamScheme,
    User
)
from app.services.notification_service import send_notification
from app.schemas.NotificationsSchema import ReqBlockedNotificationSchema, ReqDisabledNotificationDataSchema, LowBalanceNotificationSchema, LowBalanceNotificationDataSchema
from app.schemas.v2.ExternalTransactionScheme import GetOutboundFiltersResponse
from app.utils.crypto import encrypt_fernet
from io import BytesIO

logger = logging.getLogger(__name__)


async def get_bank_detail_for_merchant_(
        type: str,
        merchant_id: str,
        merchant_transaction_id: str,
        payer_id: str,
        request_id: str,
        amount: int | None,
        session: AsyncSession,
        is_vip: bool = False,
        is_whitelist: bool = False,
        bank: str | None = None,
        banks: Optional[List[str]] = None,
        types: Optional[List[str]] = None,
        payment_systems: Optional[List[str]] = None,
        initial_amount: int | None = None,
        final: bool = False
) -> ETs.ResponseInboundGetTeamBankDetail | ETs.ResponseOutboundGetTeamBankDetail:
    #block_query = (
    #    select(BankDetailModel)
    #    .where(BankDetailModel.auto_managed == true(),
    #           BankDetailModel.is_deleted == false(),
    #           BankDetailModel.is_active == true())
    #    .with_for_update()
    #)
    #block = await session.execute(block_query)
    is_whitelist = min(is_whitelist, is_vip)
    if bank:
        bank_condition = f"AND BD.bank = '{bank}'"
    elif banks:
        banks_list = ', '.join(f"'{b}'" for b in banks)
        bank_condition = f"AND BD.bank IN ({banks_list})"
    else:
        bank_condition = ""

    if type:
        type_condition = f"AND BD.type = '{type}' AND TWC.type = '{type}'"
    elif types:
        types_list = ', '.join(f"'{t}'" for t in types)
        type_condition = f"AND BD.type IN ({types_list}) AND TWC.type IN ({types_list})"
    else:
        type_condition = ""

    if payment_systems:
        payment_list = ', '.join(f"'{p}'" for p in payment_systems)
        payment_condition = f"AND BD.payment_system IN ({payment_list})"
    else:
        payment_condition = ""

    for_auto_managed = f"""AND (
        BD.auto_managed = FALSE OR (
            BD.auto_managed = TRUE
            AND (
                BD.max_pending_count IS NULL
                OR BD.pending_count < BD.max_pending_count
            )
            AND BD.max_today_amount_used >= (
                CASE WHEN BD.last_transaction_timestamp::date < CURRENT_DATE THEN 0
                     ELSE BD.today_amount_used
                END
            ) + {amount // DECIMALS}
            AND BD.max_today_transactions_count > (
                CASE WHEN BD.last_transaction_timestamp::date < CURRENT_DATE THEN BD.pending_count
                     ELSE BD.today_transactions_count + BD.pending_count
                END
            )
            AND CURRENT_TIME BETWEEN BD.period_start_time AND BD.period_finish_time
            AND (
                BD.max_pending_count > 1
                OR (
                    BD.last_accept_timestamp IS NULL
                    OR BD.last_accept_timestamp < (CURRENT_TIMESTAMP - (BD.delay || ' minutes')::interval)
                )
            )
        )
    )"""

    if is_vip:
        if is_whitelist:
            where_additional = """
            AND (
                WPM.payer_id IS NOT NULL OR BD.is_vip = FALSE
            )
            AND (
                BD.is_vip = FALSE
                OR (
                    BD.is_vip = TRUE AND (
                        BD.profile_id = VPM.bank_detail_id
                        OR BD.count_vip_payers < BD.max_vip_payers
                    )
                )
            )
            """
        else:
            where_additional = """
            AND (
                BD.is_vip = FALSE
                OR (
                    BD.is_vip = TRUE AND (
                        BD.profile_id = VPM.bank_detail_id
                        OR BD.count_vip_payers < BD.max_vip_payers
                    )
                )
            )
            """
    else:
        where_additional = "AND BD.is_vip = FALSE"

    whitelist_condition = f"""
    LEFT JOIN whitelist_payer_id_model WPM 
        ON WPM.payer_id = '{payer_id}'
    """
    await session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": amount})
    bank_details_q = await session.execute(
        text(
            f"""
            SELECT
                BD.id AS bank_detail_id,
                BD.team_id,
                BD.is_vip,
                TWC.inbound_traffic_weight,
                merchants.currency_id,
                BD.update_timestamp,
                -log(RANDOM()) / TWC.inbound_traffic_weight AS sort,
                teams.priority_inbound,
                VPM.bank_detail_id AS existing_vip_bank,
                BD.profile_id
            FROM bank_detail_model BD
            LEFT JOIN external_transaction_model T
                ON T.bank_detail_id = BD.id 
                AND T.status = '{Status.PENDING}'
                AND T.amount = {amount}
            INNER JOIN traffic_weight_contact_model TWC ON TWC.team_id = BD.team_id
            INNER JOIN teams ON teams.id = BD.team_id
            INNER JOIN user_model team_user ON team_user.id = BD.team_id
            INNER JOIN merchants ON merchants.id = '{merchant_id}'
            INNER JOIN geo_settings gs ON teams.geo_id = gs.id
            LEFT JOIN user_balance_change_nonce_model nm ON nm.balance_id = team_user.balance_id
            LEFT JOIN vip_payer_model VPM 
            ON VPM.payer_id = '{payer_id}'
               AND VPM.bank_detail_id = BD.profile_id
            {whitelist_condition}
            WHERE BD.is_deleted = FALSE
              AND BD.is_active = TRUE
              AND teams.is_inbound_enabled = TRUE
              AND team_user.is_blocked = FALSE
              AND TWC.is_deleted = FALSE
              AND TWC.inbound_traffic_weight > 0
              AND teams.priority_inbound != 0
              {for_auto_managed}
              AND BD.fiat_max_inbound * {DECIMALS} >= {amount}
              AND BD.fiat_min_inbound * {DECIMALS} <= {amount}
              AND (nm.trust_balance >= teams.credit_factor * {DECIMALS}
                   OR (nm.trust_balance is null AND teams.credit_factor <= 0))
              AND teams.fiat_max_inbound * {DECIMALS} >= {amount}
              AND teams.fiat_min_inbound * {DECIMALS} <= {amount}
              AND TWC.merchant_id = '{merchant_id}'
              AND T.bank_detail_id IS NULL
              AND (
                  teams.max_inbound_pending_per_token IS NULL OR
                  teams.count_pending_inbound < teams.max_inbound_pending_per_token
              )
              AND (NOT BD.need_check_automation OR (BD.pending_count <= gs.req_after_enable_max_pay_in_count))
              {type_condition}
              {bank_condition}
              {payment_condition}
              {where_additional}
            ORDER BY 
                CASE WHEN VPM.bank_detail_id IS NOT NULL THEN 0 ELSE 1 END,
                BD.is_vip DESC,
                teams.priority_inbound DESC,
                sort,
                BD.update_timestamp,
                BD.team_id DESC
            LIMIT 1
            """
        )
    )

    result = bank_details_q.first()

    if result is None:
        if final:
            if bank is None and banks and len(banks) == 1:
                bank = banks[0]
            if type is None and types and len(types) == 1:
                type = types[0]
            if payment_systems and len(payment_systems) == 1:
                payment_system = payment_systems[0]
            else:
                payment_system = None
            current_time = int(datetime.utcnow().timestamp())
            unique_id = str(uuid.uuid4())
            error_key = f"/count/errors/450/{merchant_id}/{type}/{bank}/{payment_system}/{str(is_vip).lower()}"
            await redis.rediss.zadd(
                error_key,
                {f"{current_time}:{unique_id}": current_time}
            )
            await redis.rediss.sadd(f"/count/errors/450/index/{merchant_id}", error_key)
            log_data = AllTeamsDisabledLogSchema(
                request_id=request_id,
                merchant_id=merchant_id,
                payer_id=payer_id,
                amount=initial_amount,
                type=type,
                bank=bank,
                banks=banks,
                types=types,
                payment_systems=payment_systems,
                is_vip=is_vip,
                is_whitelist=is_whitelist,
                merchant_transaction_id=merchant_transaction_id,
            )
            logger.info(log_data.model_dump_json())
            logger.info(
                f"[AllTeamsDisabledException] - payer_id = {payer_id}, merchant_id = {merchant_id}, amount = {initial_amount}, type = {type}, bank = {bank}, banks = {banks}, types = {types}, payment_systems = {payment_systems}, is_vip = {is_vip}, is_whitelist = {is_whitelist}, merchant_transaction_id = {merchant_transaction_id}"
            )

        raise exceptions.AllTeamsDisabledException()

    b_d_id, team_id, is_bd_vip, _, currency_id, _, _, _, existing_vip_bank, profile_id = result

    await session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"), {"lock_key": int(UUID(b_d_id).int & 0x7FFFFFFFFFFFFFFF)})
    if is_vip and is_bd_vip:
        now = datetime.utcnow()

        if existing_vip_bank is not None:
            stmt = (
                update(VipPayerModel)
                .where(
                    VipPayerModel.payer_id == payer_id,
                    VipPayerModel.bank_detail_id == profile_id
                )
                .values(last_transaction_timestamp=now)
            )
            await session.execute(stmt)
        else:
            try:
                stmt = text("""
                    UPDATE bank_detail_model
                    SET count_vip_payers = count_vip_payers + 1
                    WHERE profile_id = :profile_id AND count_vip_payers < max_vip_payers
                    RETURNING id
                """)
                result = await session.execute(stmt, {"profile_id": profile_id})
                updated_ids = result.scalars().all()

                if not updated_ids:
                    if final:
                        if bank is None and banks and len(banks) == 1:
                            bank = banks[0]
                        if type is None and types and len(types) == 1:
                            type = types[0]
                        if payment_systems and len(payment_systems) == 1:
                            payment_system = payment_systems[0]
                        else:
                            payment_system = None
                        current_time = int(datetime.utcnow().timestamp())
                        unique_id = str(uuid.uuid4())
                        error_key = f"/count/errors/450/{merchant_id}/{type}/{bank}/{payment_system}/{str(is_vip).lower()}"
                        await redis.rediss.zadd(
                            error_key,
                            {f"{current_time}:{unique_id}": current_time}
                        )
                        await redis.rediss.sadd(f"/count/errors/450/index/{merchant_id}", error_key)
                        log_data = AllTeamsDisabledLogSchema(
                            request_id=request_id,
                            merchant_id=merchant_id,
                            payer_id=payer_id,
                            amount=initial_amount,
                            type=type,
                            bank=bank,
                            banks=banks,
                            types=types,
                            payment_systems=payment_systems,
                            is_vip=is_vip,
                            is_whitelist=is_whitelist,
                            merchant_transaction_id=merchant_transaction_id,
                        )
                        logger.info(log_data.model_dump_json())
                        logger.info(
                            f"[AllTeamsDisabledException] - payer_id = {payer_id}, merchant_id = {merchant_id}, amount = {initial_amount}, type = {type}, bank = {bank}, banks = {banks}, types = {types}, payment_systems = {payment_systems}, is_vip = {is_vip}, is_whitelist = {is_whitelist}, merchant_transaction_id = {merchant_transaction_id}"
                        )
                    raise exceptions.AllTeamsDisabledException()

                stmt = pg_insert(VipPayerModel).values(
                    payer_id=payer_id,
                    bank_detail_id=profile_id,
                    last_transaction_timestamp=now
                )
                await session.execute(stmt)
            except DBAPIError as e:
                if "VIP payer has reached max allowed bank_detail links" in str(e.orig):
                    if final:
                        if bank is None and banks and len(banks) == 1:
                            bank = banks[0]
                        if type is None and types and len(types) == 1:
                            type = types[0]
                        if payment_systems and len(payment_systems) == 1:
                            payment_system = payment_systems[0]
                        else:
                            payment_system = None
                        current_time = int(datetime.utcnow().timestamp())
                        unique_id = str(uuid.uuid4())
                        error_key = f"/count/errors/450/{merchant_id}/{type}/{bank}/{payment_system}/{str(is_vip).lower()}"
                        await redis.rediss.zadd(
                            error_key,
                            {f"{current_time}:{unique_id}": current_time}
                        )
                        await redis.rediss.sadd(f"/count/errors/450/index/{merchant_id}", error_key)
                        log_data = AllTeamsDisabledLogSchema(
                            request_id=request_id,
                            merchant_id=merchant_id,
                            payer_id=payer_id,
                            amount=initial_amount,
                            type=type,
                            bank=bank,
                            banks=banks,
                            types=types,
                            payment_systems=payment_systems,
                            is_vip=is_vip,
                            is_whitelist=is_whitelist,
                            merchant_transaction_id=merchant_transaction_id,
                        )
                        logger.info(log_data.model_dump_json())
                        logger.info(
                            f"[AllTeamsDisabledException] - payer_id = {payer_id}, merchant_id = {merchant_id}, amount = {initial_amount}, type = {type}, bank = {bank}, banks = {banks}, types = {types}, payment_systems = {payment_systems}, is_vip = {is_vip}, is_whitelist = {is_whitelist}, merchant_transaction_id = {merchant_transaction_id}"
                        )
                    raise exceptions.AllTeamsDisabledException()
                raise e

    bank_detail_q = await session.execute(
        select(BankDetailModel).filter(
            BankDetailModel.id == b_d_id,
        )
    )

    bank_detail = bank_detail_q.scalars().first()

    if bank_detail is None:
        raise exceptions.BankDetailNotFoundException()

    bank_detail.update_timestamp = func.now()

    return ETs.ResponseInboundGetTeamBankDetail(
        currency_id=currency_id,
        team_id=team_id,
        bank_detail=ETs.BankDetailResponse(
            **bank_detail.__dict__,
            bank_icon_url=f"/payment-form/bank-icon/{bank_detail.bank}",
        ),
    )


async def get_team_for_merchant_(
        merchant_id: str, amount: int | None, session: AsyncSession
) -> ETs.ResponseOutboundGetTeamBankDetail:
    bank_details_q = await session.execute(
        text(
            f"""
    SELECT TWC.team_id,
           TWC.currency_id,
           TWC.outbound_traffic_weight
        FROM traffic_weight_contact_model TWC
                 INNER JOIN user_model
                            ON user_model.id = TWC.team_id
        WHERE user_model.is_outbound_enabled = true
        AND user_model.is_blocked = FALSE
        AND TWC.merchant_id = '{merchant_id}'
        AND TWC.is_deleted = FALSE;
                """
        )
    )
    contracts_bank_details = bank_details_q.all()
    teams = []
    weights = []
    currency_ids = []
    for team_id, currency_id, o_t_w in contracts_bank_details:
        teams.append(team_id)
        weights.append(o_t_w)
        currency_ids.append(currency_id)
    if len(teams) == 0:
        raise exceptions.AllTeamsDisabledException()
    try:
        team_index = random.choices(range(0, len(teams)), weights=weights)[0]
    except ValueError:
        raise exceptions.AllTeamsDisabledException()
    team_id = teams[team_index]
    currency_id = currency_ids[team_index]
    return ETs.ResponseOutboundGetTeamBankDetail(
        currency_id=currency_id, team_id=team_id
    )


async def add_whitelist(
    request: WhiteListPayerAddRequest,
    merchant_id: str,
):
    if not request.payer_ids:
        return {"message": "Empty payer_ids"}

    values = ", ".join(
        f"('{payer_id}')" for payer_id in request.payer_ids
    )

    query = text(f"""
        INSERT INTO whitelist_payer_id_model (payer_id)
        VALUES {values}
        ON CONFLICT DO NOTHING
    """)

    async with async_session() as session:
        await session.execute(query)
        await session.commit()

    return {"message": "Payers added to whitelist (new only)"}


# async def get_team_for_merchant(
#         request: ETs.RequestGetBankDetailDB,
# ) -> ETs.ResponseInboundGetTeamBankDetail | ETs.ResponseOutboundGetTeamBankDetail:
#     async with async_session() as session:
#         if request.is_inbound:
#             return await get_bank_detail_for_merchant_(
#                 type=request.type,
#                 merchant_id=request.merchant_id,
#                 amount=request.amount,
#                 session=session)
#         else:
#             return await get_team_for_merchant_(
#                 merchant_id=request.merchant_id,
#                 amount=request.amount,
#                 session=session)


async def _change_trust_locked_balances(
        session: AsyncSession,
        transaction_model: ExternalTransactionModel,
        is_add_locked: bool,
) -> None:
    await session.flush()
    user_id: str | None = None
    if transaction_model.direction == Direction.INBOUND:
        user_id = transaction_model.team_id

    if transaction_model.direction == Direction.OUTBOUND:
        user_id = transaction_model.merchant_id

    if user_id is None:
        raise exceptions.UserNotFoundException

    balance_id = await get_balance_id_by_user_id(user_id=user_id, session=session)
    balance_change = {
        "transaction_id": transaction_model.id,
        "user_id": user_id,
        "balance_id": balance_id,
    }
    if transaction_model.economic_model in (
            EconomicModel.CRYPTO,
            EconomicModel.CRYPTO_FIAT_PROFIT,
    ):
        usdt_value: int = (
                transaction_model.amount * DECIMALS // transaction_model.exchange_rate
        )
        balance_change.update(
            {
                "trust_balance": -usdt_value if is_add_locked else usdt_value,
                "locked_balance": usdt_value if is_add_locked else -usdt_value,
                "fiat_trust_balance": (
                    -transaction_model.amount
                    if is_add_locked
                    else transaction_model.amount
                ),
                "fiat_locked_balance": (
                    transaction_model.amount
                    if is_add_locked
                    else -transaction_model.amount
                ),
            }
        )
    elif transaction_model.economic_model in (
            EconomicModel.FIAT,
            EconomicModel.FIAT_CRYPTO_PROFIT,
    ):
        balance_change.update(
            {
                "fiat_trust_balance": (
                    -transaction_model.amount
                    if is_add_locked
                    else transaction_model.amount
                ),
                "fiat_locked_balance": (
                    transaction_model.amount
                    if is_add_locked
                    else -transaction_model.amount
                ),
            }
        )
    else:
        return None
    await add_balance_changes(session, [balance_change])


async def find_external_transaction_by_id(transaction_id: str, merchant_id: str):
    async with ro_async_session() as session:
        contract_req = await session.execute(
            select(
                ExternalTransactionModel,
            ).filter(
                ExternalTransactionModel.id == transaction_id,
                ExternalTransactionModel.merchant_id == merchant_id,
            )
        )
        r = contract_req.scalars().first()
        if r is None:
            raise exceptions.ExternalTransactionNotFoundException()
        user_req = await session.execute(
            select(
                UserModel.transaction_auto_close_time_s,
            ).filter(
                UserModel.id == r.team_id,
            )
        )
        close_time = user_req.fetchone()[0]
        return ETs.PaymentFormResponse(**r.__dict__, bank_icon_url=None, transaction_auto_close_time_s=close_time)


async def find_external_transaction_by(
        merchant_id: str,
        transaction_id: str | None = None,
        merchant_transaction_id: str | None = None,
):
    if merchant_transaction_id is None and transaction_id is None:
        raise exceptions.ExternalTransactionNotFoundException()

    async with ro_async_session() as session:
        contract_req = await session.execute(
            select(ExternalTransactionModel).filter(
                (
                    ExternalTransactionModel.id == transaction_id
                    if transaction_id is not None
                    else ExternalTransactionModel.merchant_transaction_id
                         == merchant_transaction_id
                ),
                ExternalTransactionModel.merchant_id == merchant_id,
            )
        )
        result = contract_req.scalars().first()
        if result is None:
            raise exceptions.ExternalTransactionNotFoundException()
        return result


async def get_team_by_transaction_id(id: str):
    async with async_session() as session:
        contract_req = await session.execute(
            select(
                ExternalTransactionModel.id,
                ExternalTransactionModel.direction,
                ExternalTransactionModel.status,
                ExternalTransactionModel.merchant_transaction_id,
                ExternalTransactionModel.bank_detail_number,
                ExternalTransactionModel.amount,
                ExternalTransactionModel.team_id,
                ExternalTransactionModel.bank_detail_bank,
                ExternalTransactionModel.bank_detail_name,
            ).filter(
                or_(
                    ExternalTransactionModel.id == id,
                    ExternalTransactionModel.merchant_transaction_id == id,
                ),
                ExternalTransactionModel.merchant_id == UserModel.id,
                UserModel.namespace == 'choza'
            )
        )
        trx_bd = contract_req.first()
        if trx_bd is None:
            raise exceptions.ExternalTransactionNotFoundException()
        (
            trx_id,
            trx_dir,
            trx_status,
            m_trx_id,
            trx_bd_n,
            trx_amount,
            trx_t_id,
            bd_b,
            bd_n,
        ) = trx_bd
        if trx_t_id is not None:
            user = await session.execute(
                select(UserModel).filter(
                    trx_t_id == UserModel.id,
                )
            )
            if user is None:
                raise exceptions.UserNotFoundException()
            result = user.scalars().first()

            return UserIdNameResponse(
                status=trx_status,
                direction=trx_dir,
                id=trx_id,
                name=result.name,
                transaction_id=trx_id,
                merchant_transaction_id=m_trx_id,
                bank_detail_number=trx_bd_n,
                bank_detail_bank=bd_b,
                bank_detail_name=bd_n,
                amount=trx_amount,
                telegram_appeal_chat_id=result.telegram_appeal_chat_id,
                telegram_bot_secret=result.telegram_bot_secret,
            )
        else:
            return UserIdNameResponse(
                status=trx_status,
                direction=trx_dir,
                id=trx_id,
                name=None,
                transaction_id=trx_id,
                merchant_transaction_id=m_trx_id,
                bank_detail_number=trx_bd_n,
                bank_detail_bank=bd_b,
                bank_detail_name=bd_n,
                amount=trx_amount,
                telegram_appeal_chat_id=None,
                telegram_bot_secret=None,
            )


async def find_external_transaction_status(
        transaction_id: str, merchant_id: str
) -> ETs.StatusResponse:
    async with async_session() as session:
        contract_req = await session.execute(
            select(ExternalTransactionModel.status).filter(
                ExternalTransactionModel.id == transaction_id,
                merchant_id == ExternalTransactionModel.merchant_id,
            )
        )
        status = contract_req.scalars().first()
        if status is None:
            raise exceptions.ExternalTransactionNotFoundException()
        return ETs.StatusResponse(status=status)


async def get_user_info(user_id: str, session: AsyncSession):
    economic_model_req = await session.execute(
        select(
            UserModel.economic_model, UserModel.transaction_auto_close_time_s
        ).filter(UserModel.id == user_id)
    )
    economic_model, transaction_auto_close_time_s = economic_model_req.first()
    if economic_model is None:
        raise exceptions.UnableToFindEconomicModel()
    return economic_model, transaction_auto_close_time_s


async def external_transaction_create_(
        create: ETs.RequestCreateDB,
        session: AsyncSession,
        request_id: str,
        id: Optional[str] = None
) -> ETs.Response:
    status: str = create.status
    if create.merchant_transaction_id is not None:
        m_t_q = await session.execute(
            select(ExternalTransactionModel.merchant_transaction_id)
            .filter(
                create.merchant_transaction_id
                == ExternalTransactionModel.merchant_transaction_id
            )
            .limit(1)
        )
        m_t = m_t_q.scalars().first()
        if m_t is not None:
            raise exceptions.ExternalTransactionDuplicateMerchantTransactionIdException()

    if create.direction == Direction.INBOUND:
        trx_count_q = await session.execute(
            select(func.count())
            .filter(
                ExternalTransactionModel.merchant_payer_id == create.merchant_payer_id,
                ExternalTransactionModel.status == Status.PENDING,
                ExternalTransactionModel.direction == create.direction,
            )
            .limit(Limit.FRAUD_MAX_PENDING)
        )
        trx_count = trx_count_q.scalars().first()
        if trx_count >= Limit.FRAUD_MAX_PENDING:
            raise exceptions.FraudDetectedException()

    if status not in (Status.PENDING, Status.OPEN):
        raise exceptions.ExternalTransactionRequestStatusException(
            statuses=[Status.PENDING, Status.OPEN]
        )
    currency: CurrencyModel = await _get_currency(
        currency_id=create.currency_id, session=session
    )

    if not currency:
        raise exceptions.CurrencyNotFoundException()

    tag_id = None
    if create.tag_code is not None:
        existing_tag_id = (await session.execute(
            select(TagModel.id)
            .where(TagModel.code == create.tag_code)
        )).scalars().first()

        if existing_tag_id is not None:
            tag_id = existing_tag_id

    create.currency_id = currency.name
    etm_dict = create.__dict__
    del etm_dict["tag_code"]
    extra_data = {}

    if id:
        extra_data["id"] = id

    transaction_model: ExternalTransactionModel = ExternalTransactionModel(
        **etm_dict,
        **extra_data,
        is_approved=False,
        exchange_rate=(
            currency.inbound_exchange_rate
            if create.direction == Direction.INBOUND
            else currency.outbound_exchange_rate
        ),
        tag_id=tag_id
    )
    create_timestamp = datetime.utcnow()
    delta_seconds = (FUTURE_DATE - create_timestamp).total_seconds()
    transaction_model.priority = -int(delta_seconds)
    session.add(transaction_model)
    await _change_trust_locked_balances(session, transaction_model, is_add_locked=True)

    user_id: str = (
        transaction_model.team_id
        if transaction_model.direction == Direction.INBOUND
        else transaction_model.merchant_id
    )

    if create.direction == Direction.INBOUND:
        credit_factor = await get_credit_factor_(user_id=user_id, session=session)
        current_balance = await get_balances(user_id=create.merchant_id,
                                             session=session)
        if (credit_factor * DECIMALS > current_balance[0]):
            await send_notification(LowBalanceNotificationSchema(
                team_id=user_id,
                data=LowBalanceNotificationDataSchema(
                    limit=credit_factor
                )
            ))

    if create.direction == Direction.OUTBOUND:
        credit_factor = await get_credit_factor_(user_id=create.merchant_id, session=session)
        current_balance = await get_balances(user_id=create.merchant_id,
                                             session=session)
        print(current_balance[0], current_balance[0]
              - transaction_model.amount * DECIMALS // transaction_model.exchange_rate)
        if (credit_factor * DECIMALS > current_balance[0]
                - transaction_model.amount * DECIMALS / transaction_model.exchange_rate):
            raise exceptions.TrustBalanceNotEnoughException()
    await session.commit()
    await session.refresh(transaction_model)

    async def after_trx_creation_task():
        async with async_session() as parallel_session:
            # await get_balances(
            #     user_id=user_id,
            #     session=parallel_session,
            # )
            await parallel_session.commit()
            await merchant_callback(
                hook_uri=transaction_model.hook_uri,
                direction=transaction_model.direction,
                merchant_id=transaction_model.merchant_id,
                transaction_id=transaction_model.id,
                amount=transaction_model.amount,
                status=transaction_model.status,
                request_id=request_id,
                merchant_transaction_id=transaction_model.merchant_transaction_id,
                currency_id=transaction_model.currency_id,
                exchange_rate=transaction_model.exchange_rate
            )

    asyncio.ensure_future(after_trx_creation_task())
    return ETs.Response(
        **transaction_model.__dict__,
    )


async def close_after_timeout(
        transaction_id: str,
        team_id: str,
        transaction_auto_close_time_s: int = AUTO_CLOSE_EXTERNAL_TRANSACTIONS_S,
):
    await asyncio.sleep(transaction_auto_close_time_s)
    async with async_session() as session:
        try:
            await external_transaction_update_(
                transaction_id=transaction_id,
                session=session,
                status=Status.CLOSE,
                close_if_accept=False,
                final_status=TransactionFinalStatusEnum.TIMEOUT
            )
        except exceptions.ExternalTransactionExistingStatusException as e:
            print(transaction_id, e.status_code)


async def external_transaction_create(
        create: ETs.RequestCreateDB,
) -> ETs.Response:
    """
    only status OPEN or PENDING is allowed
    """
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        try:
            result = await external_transaction_create_(create, session=session, request_id=request_id)
        except Exception as e:
            logger.info(
                f"[CreateTransactionError] - error = {e}, create params = {create.__dict__}"
            )
            raise e
        return result


def get_search_filters(request: ETs.RequestList | ITs.RequestList):
    search_without_plus = (request.search or "").replace("+", "")
    model = (
        ExternalTransactionModel
        if type(request) is ETs.RequestList
        else InternalTransactionModel
    )
    if request.amount_from is None:
        request.amount_from = Limit.MIN_INT
    if request.amount_to is None:
        request.amount_to = Limit.MAX_INT
    if request.create_timestamp_to is None:
        request.create_timestamp_to = Limit.MAX_TIMESTAMP
    if request.create_timestamp_from is None:
        request.create_timestamp_from = Limit.MIN_TIMESTAMP
    amount_search_condition: str | None = None
    try:
        float(request.search)
        value = round(float(request.search) * DECIMALS)
        if not Limit.MIN_INT <= value <= Limit.MAX_INT:
            raise ValueError
        amount_search_condition = model.amount == value
    except (ValueError, TypeError):
        pass
    queries_none = [
        model.direction == request.direction if request.direction is not None else None,
        model.status == request.status if request.status is not None else None,
        (
            model.currency_id == request.currency_id
            if type(request) is ETs.RequestList and request.currency_id is not None
            else None
        ),
        model.amount <= request.amount_to,
        model.amount >= request.amount_from,
        model.type == request.type if type(request) is ETs.RequestList and request.type is not None else None,
        model.bank_detail_bank == request.bank if type(
            request) is ETs.RequestList and request.bank is not None else None,
        model.create_timestamp
        <= datetime.utcfromtimestamp(request.create_timestamp_to),
        model.create_timestamp
        >= datetime.utcfromtimestamp(request.create_timestamp_from),
        (
            or_(
                (
                    func.replace(model.bank_detail_number, "+", "") == search_without_plus
                    if type(request) is ETs.RequestList
                    else false()
                ),
                model.id == request.search,
                (
                    model.merchant_transaction_id == request.search
                    if type(request) is ETs.RequestList
                    else false()
                ),
                (
                    model.merchant_payer_id == request.search
                    if type(request) is ETs.RequestList
                    else false()
                ),
                (
                    amount_search_condition
                    if amount_search_condition is not None
                    else false()
                ),
                (
                    model.address == request.search
                    if type(request) is ITs.RequestList
                    else false()
                ),
                (
                    model.blockchain_transaction_hash == request.search
                    if type(request) is ITs.RequestList
                    else false()
                ),
            )
            if request.search is not None
            else None
        ),
    ]
    queries = []
    for query in queries_none:
        if query is not None:
            queries.append(query)

    return queries


async def external_transaction_list(
        request: ETs.RequestList,
        namespace_id: int | None = None
) -> ETs.ResponseList:
    queries = get_search_filters(request)
    async with ro_async_session() as session:
        query = text("""
            SELECT auto_close_outbound_transactions_s
            FROM geo_settings
            WHERE id = :geo_id
        """)

        result = await session.execute(query, {"geo_id": request.geo_id})
        row = result.fetchone()

        if row and request.direction == Direction.OUTBOUND:
            auto_close_value = row[0]
        else:
            auto_close_value = None
        if request.role == Role.SUPPORT:
            query = (
                select(
                    ExternalTransactionModel,
                    MerchantModel.name.label("merchant_name"),
                    case(
                        (ExternalTransactionModel.team_id.is_(None), None),
                        else_=TeamModel.name
                    ).label("team_name"),
                    MerchantModel.transaction_auto_close_time_s,
                    MerchantModel.transaction_outbound_auto_close_time_s,
                    MessageModel.text,
                    TagModel.code.label("tag_code"),
                    BankDetailModel.comment,
                    BankDetailModel.alias,
                    GeoSettingsModel.auto_close_outbound_transactions_s
                )
                #.distinct()
                .outerjoin(
                    TeamModel,
                    TeamModel.id == ExternalTransactionModel.team_id
                )
                .join(
                    MerchantModel,
                    MerchantModel.id == ExternalTransactionModel.merchant_id,
                ).join(
                    GeoSettingsModel,
                    GeoSettingsModel.id == MerchantModel.geo_id
                )
                .outerjoin(
                    MessageModel,
                    MessageModel.external_transaction_id == ExternalTransactionModel.id
                )
                .join(
                    TagModel,
                    TagModel.id == ExternalTransactionModel.tag_id
                )
                .outerjoin(
                    BankDetailModel,
                    ExternalTransactionModel.bank_detail_id == BankDetailModel.id
                )
                .filter(
                    ExternalTransactionModel.priority > request.last_priority,
                    (
                        ExternalTransactionModel.direction == request.direction
                        if request.direction is not None
                        else true()
                    ),
                    (
                        MerchantModel.namespace_id == namespace_id
                        if request.role == Role.SUPPORT
                        else true()
                    ),
                    (
                        MerchantModel.geo_id == request.geo_id
                        if request.geo_id is not None and request.role == Role.SUPPORT
                        else true()
                    ),
                    (
                        ExternalTransactionModel.merchant_id == request.merchant_id
                        if request.merchant_id is not None
                        else true()
                    ),
                    (
                        ExternalTransactionModel.team_id == request.team_id
                        if request.team_id is not None
                        else true()
                    ),
                    (
                        ExternalTransactionModel.final_status == request.final_status
                        if request.final_status is not None
                        else true()
                    )
                )
                .filter(*queries)
                .order_by(ExternalTransactionModel.priority)
                .limit(request.limit)
            )

            # compiled_query = query.compile(
            #     dialect=postgresql.dialect(),
            #     compile_kwargs={"literal_binds": True}
            # )
            # print(str(compiled_query))

            trx_list = await session.execute(query)
            result = [
                ETs.Response(
                    **{
                        **{
                            k: v
                            for k, v in i[0].__dict__.items()
                            if k != "bank_detail_bank"
                        },
                        "bank_detail_bank": (
                            ASSOCIATE_BANK.get(i[0].bank_detail_bank, i[0].bank_detail_bank)
                            if request.direction == "outbound"
                            else i[0].bank_detail_bank
                        )
                    },
                    merchant_name=i[1],
                    team_name=i[2],
                    transaction_auto_close_time_s=i[3],
                    transaction_outbound_auto_close_time_s=i[4],
                    text=i[5],
                    tag_code=i[6],
                    comment=i[7] if request.direction == 'inbound' else None,
                    alias=i[8] if request.direction == 'inbound' else None,
                    auto_close_outbound_transactions_s=i[9] if request.direction == "outbound" else None
                )
                for i in trx_list
            ]
            if len(result) > request.limit:
                result = result[:request.limit]
            return ETs.ResponseList(items=result)
        else:
            query = (
                select(
                    ExternalTransactionModel,
                    MerchantModel.transaction_auto_close_time_s,
                    MerchantModel.transaction_outbound_auto_close_time_s,
                    TagModel.code.label("tag_code"),
                    MessageModel.text,
                    BankDetailModel.alias
                )
                #.distinct()
                .join(
                    MerchantModel,
                    ExternalTransactionModel.merchant_id == MerchantModel.id
                )
                .outerjoin(
                    MessageModel,
                    MessageModel.external_transaction_id == ExternalTransactionModel.id
                ).outerjoin(
                    BankDetailModel,
                    ExternalTransactionModel.bank_detail_id == BankDetailModel.id
                )
                .filter(
                    (
                        ExternalTransactionModel.merchant_id == request.user_id
                        if request.role == Role.MERCHANT
                        else ExternalTransactionModel.team_id == request.user_id
                    ),
                    ExternalTransactionModel.priority > request.last_priority,
                    (
                        ExternalTransactionModel.direction == request.direction
                        if request.direction is not None
                        else true()
                    ),
                )
                .join(
                    TagModel,
                    TagModel.id == ExternalTransactionModel.tag_id
                )
                .filter(*queries)
                .order_by(ExternalTransactionModel.priority)
                .limit(request.limit)
            )
            trx_list = await session.execute(query)
            result = [
                ETs.Response(
                    **{
                        **{
                            k: v
                            for k, v in i[0].__dict__.items()
                            if k != "bank_detail_bank"
                        },
                        "bank_detail_bank": (
                            ASSOCIATE_BANK.get(i[0].bank_detail_bank, i[0].bank_detail_bank)
                            if request.direction == "outbound"
                            else i[0].bank_detail_bank
                        )
                    },
                    transaction_auto_close_time_s=i[1],
                    transaction_outbound_auto_close_time_s=i[2],
                    tag_code=i[3] if request.role == Role.MERCHANT else None,
                    text=i[4],
                    alias=i[5],
                    auto_close_outbound_transactions_s=auto_close_value if request.direction == "outbound" else None
                )
                for i in trx_list
            ]
            if len(result) > request.limit:
                result = result[:request.limit]

            return ETs.ResponseList(items=result)


async def external_transaction_close_(
        transaction_id: str,
        session: AsyncSession,
        team_id: str | None = None,
        merchant_id: str | None = None,
        new_amount: int | None = None
) -> ETs.Response:
    request_id = str(uuid.uuid4())
    transaction_model: ExternalTransactionModel = (
        await _find_external_transaction_by_id(
            transaction_id=transaction_id,
            session=session,
        )
    )

    if transaction_model.status not in (Status.PENDING, Status.PROCESSING):
        raise exceptions.ExternalTransactionExistingStatusException(
            statuses=[Status.PENDING, Status.PROCESSING]
        )

    if transaction_model.status in (Status.PENDING, Status.PROCESSING):
        await _change_trust_locked_balances(
            session, transaction_model, is_add_locked=False
        )

    if new_amount is not None and new_amount != transaction_model.amount:
        transaction_model.amount = new_amount

    transaction_model.status = Status.CLOSE
    create_timestamp = transaction_model.create_timestamp
    delta_seconds = (FUTURE_DATE - create_timestamp).total_seconds()
    transaction_model.priority = int(delta_seconds)
    transaction_model.final_status_timestamp = datetime.utcnow()
    await session.commit()

    async def after_trx_creation_task():
        async with async_session() as parallel_session:
            # await get_balances(
            #     user_id=transaction_model.merchant_id
            #     if transaction_model.direction == Direction.OUTBOUND
            #     else transaction_model.team_id,
            #
            #     session=parallel_session,
            # )
            await parallel_session.commit()

    asyncio.ensure_future(after_trx_creation_task())

    await merchant_callback(
        hook_uri=transaction_model.hook_uri,
        direction=transaction_model.direction,
        merchant_id=transaction_model.merchant_id,
        transaction_id=transaction_model.id,
        amount=transaction_model.amount,
        status=transaction_model.status,
        merchant_transaction_id=transaction_model.merchant_transaction_id,
        request_id=request_id,
        merchant_trust_change=0,
        currency_id=transaction_model.currency_id,
        exchange_rate=transaction_model.exchange_rate
    )
    return ETs.Response(
        **transaction_model.__dict__,
    )


async def external_transaction_update_(
        transaction_id: str,
        session: AsyncSession,
        merchant_transaction_id: str | None = None,
        new_amount: int | None = None,
        reason: str | None = None,
        status: str = Status.ACCEPT,
        close_if_accept=True,
        final_status: TransactionFinalStatusEnum | None = None,
        from_device: bool = False
) -> ETs.Response:
    request_id = str(uuid.uuid4())
    transaction_model: ExternalTransactionModel = (
        await _find_external_transaction_by_id(
            transaction_id=transaction_id,
            merchant_transaction_id=merchant_transaction_id,
            session=session,
        )
    )

    if not close_if_accept and transaction_model.status != Status.PENDING:
        raise exceptions.ExternalTransactionExistingStatusException(statuses=[Status.PENDING])

    if new_amount is None:
        new_amount = transaction_model.amount

    if not final_status:
        if status == Status.ACCEPT:
            if new_amount != transaction_model.amount:
                final_status = TransactionFinalStatusEnum.RECALC
            else:
                final_status = TransactionFinalStatusEnum.ACCEPT
        
        if status == Status.CLOSE:
            final_status = TransactionFinalStatusEnum.CANCEL

    if final_status:
        transaction_model.final_status = final_status

    initial_status = transaction_model.status

    if transaction_model.direction == Direction.OUTBOUND and initial_status != status and status == Status.CLOSE:
        await session.execute(
            update(TeamModel)
            .where(TeamModel.id == transaction_model.team_id)
            .values(
                today_outbound_amount_used=case(
                    (func.date(TeamModel.last_transaction_timestamp) < func.date(func.now()),
                     0),
                    else_=TeamModel.today_outbound_amount_used - (transaction_model.amount // DECIMALS)
                ),
            )
        )

    transaction_model.reason = reason

    if status == Status.CLOSE and transaction_model.status in (
            Status.PENDING,
            Status.PROCESSING,
            Status.CLOSE
    ):
        if transaction_model.status in (Status.PENDING, Status.PROCESSING):
            await _change_trust_locked_balances(
                session, transaction_model, is_add_locked=False
            )

        if new_amount != transaction_model.amount:
            transaction_model.amount = new_amount

        transaction_model.status = Status.CLOSE
        create_timestamp = transaction_model.create_timestamp
        delta_seconds = (FUTURE_DATE - create_timestamp).total_seconds()
        transaction_model.priority = int(delta_seconds)
        transaction_model.final_status_timestamp = datetime.utcnow()
        if initial_status == Status.PENDING and status == Status.CLOSE:
            stmt = (
                update(BankDetailModel)
                .where(BankDetailModel.id == transaction_model.bank_detail_id,
                    BankDetailModel.pending_count > 0)
                .values(pending_count=BankDetailModel.pending_count - 1,
                        today_amount_used=case(
                            (BankDetailModel.today_amount_used < (transaction_model.amount // DECIMALS),
                             0),
                            else_=BankDetailModel.today_amount_used - (transaction_model.amount // DECIMALS)
                        )
                )
            )
            await session.execute(stmt)
            stmt2 = (
                update(TeamModel)
                .where(TeamModel.id == transaction_model.team_id,
                       TeamModel.count_pending_inbound > 0)
                .values(count_pending_inbound=TeamModel.count_pending_inbound - 1)
            )
            await session.execute(stmt2)

        await session.commit()

        async def after_trx_creation_task():
            async with async_session() as parallel_session:
                # if transaction_model.team_id is not None or transaction_model.direction != Direction.OUTBOUND:
                #     await get_balances(
                #         user_id=transaction_model.team_id,
                #         session=parallel_session,
                #     )
                # await get_balances(
                #     user_id=transaction_model.merchant_id,
                #     session=parallel_session,
                # )
                await parallel_session.commit()

        asyncio.ensure_future(after_trx_creation_task())

        await merchant_callback(
            hook_uri=transaction_model.hook_uri,
            direction=transaction_model.direction,
            merchant_id=transaction_model.merchant_id,
            transaction_id=transaction_model.id,
            amount=transaction_model.amount,
            status=transaction_model.status,
            merchant_transaction_id=transaction_model.merchant_transaction_id,
            request_id=request_id,
            merchant_trust_change=0,
            currency_id=transaction_model.currency_id,
            exchange_rate=transaction_model.exchange_rate
        )
        return ETs.Response(
            **transaction_model.__dict__,
        )

    is_change_sum_on_inbound_accepted = False
    final_amount_on_inbound_accepted = new_amount
    if (
            transaction_model.status in Status.ACCEPT
            and new_amount is not None
    ):
        is_change_sum_on_inbound_accepted = True

        new_amount -= transaction_model.amount
        if status == Status.CLOSE:
            new_amount = -transaction_model.amount
        transaction_model.status = Status.CLOSE
        create_timestamp = transaction_model.create_timestamp
        delta_seconds = (FUTURE_DATE - create_timestamp).total_seconds()
        transaction_model.priority = int(delta_seconds)

    if transaction_model.status == Status.CLOSE:
        transaction_model.amount = new_amount
        await session.flush()

    if initial_status in (Status.PENDING, Status.PROCESSING) and transaction_model.amount != new_amount:
        print('BUUUUUUUUUUUUR')
        transaction_model.amount = new_amount - transaction_model.amount
        await _change_trust_locked_balances(transaction_model=transaction_model,
                                            is_add_locked=True, session=session)
        transaction_model.amount = new_amount

    usdt_value: int = (
            transaction_model.amount * DECIMALS // transaction_model.exchange_rate
    )

    contracts_q = await session.execute(
        select(
            (
                FeeContractModel.inbound_fee
                if transaction_model.direction == Direction.INBOUND
                else FeeContractModel.outbound_fee
            ),
            FeeContractModel.user_id,
            UserModel.balance_id,
        )
        .join(UserModel, UserModel.id == FeeContractModel.user_id)
        .filter(
            FeeContractModel.merchant_id == transaction_model.merchant_id,
            FeeContractModel.team_id == transaction_model.team_id,
            FeeContractModel.is_deleted == false(),
            FeeContractModel.tag_id == transaction_model.tag_id,
        )
    )
    update_user_balances_list = []
    total_fee_sum = 0
    agents_fee_sum = 0

    is_team_found = False
    is_merchant_found = False
    for fee, user_id, balance_id in contracts_q.all():
        update_user_balances_list.append((fee, user_id, balance_id))
        if user_id == transaction_model.merchant_id:
            is_team_found = True
        elif user_id == transaction_model.team_id:
            is_merchant_found = True
        else:
            agents_fee_sum += fee
        total_fee_sum += fee
    if not is_team_found or not is_merchant_found:
        raise exceptions.UserOrTeamNotContractNotFoundException()

    balances_changes = []
    merchant_trust_change: int | None = None
    if transaction_model.direction == Direction.INBOUND:
        for inbound_fee, user_id, balance_id in update_user_balances_list:
            profit = 0
            trust = 0
            locked = 0

            fiat_profit = 0
            fiat_trust = 0
            fiat_locked = 0

            if transaction_model.economic_model == EconomicModel.CRYPTO:
                if user_id == transaction_model.merchant_id:
                    trust = usdt_value * inbound_fee // total_fee_sum
                    merchant_trust_change = trust
                elif user_id == transaction_model.team_id:
                    profit = usdt_value * inbound_fee // total_fee_sum
                    trust, locked = (
                        (-usdt_value, 0)
                        if transaction_model.status == Status.CLOSE
                        else (0, -usdt_value)
                    )
                else:
                    profit = usdt_value * inbound_fee // total_fee_sum

            elif transaction_model.economic_model == EconomicModel.FIAT:
                if user_id == transaction_model.merchant_id:
                    fiat_trust = transaction_model.amount * inbound_fee // total_fee_sum
                elif user_id == transaction_model.team_id:
                    fiat_profit = (
                            transaction_model.amount * inbound_fee // total_fee_sum
                    )
                    fiat_trust, fiat_locked = (
                        (-transaction_model.amount, 0)
                        if transaction_model.status == Status.CLOSE
                        else (0, -transaction_model.amount)
                    )
                    fiat_trust += (
                            inbound_fee * transaction_model.amount // total_fee_sum
                    )
                else:
                    fiat_profit = (
                            transaction_model.amount * inbound_fee // total_fee_sum
                    )

            elif transaction_model.economic_model == EconomicModel.FIAT_CRYPTO_PROFIT:
                if user_id == transaction_model.merchant_id:
                    fiat_trust = transaction_model.amount * inbound_fee // total_fee_sum
                elif user_id == transaction_model.team_id:
                    fiat_profit = (
                            transaction_model.amount * inbound_fee // total_fee_sum
                    )

                    fiat_trust_locked = -transaction_model.amount
                    fiat_trust, fiat_locked = (
                        (fiat_trust_locked, 0)
                        if transaction_model.status == Status.CLOSE
                        else (0, fiat_trust_locked)
                    )
                    fiat_trust += (
                            (agents_fee_sum + inbound_fee)
                            * transaction_model.amount
                            // total_fee_sum
                    )
                    trust = -agents_fee_sum * usdt_value // total_fee_sum
                else:
                    profit = usdt_value * inbound_fee // total_fee_sum

            elif transaction_model.economic_model == EconomicModel.CRYPTO_FIAT_PROFIT:
                if user_id == transaction_model.merchant_id:
                    trust = usdt_value * inbound_fee // total_fee_sum
                    fiat_trust = transaction_model.amount * inbound_fee // total_fee_sum
                    merchant_trust_change = trust
                elif user_id == transaction_model.team_id:
                    trust, locked = (
                        (-usdt_value, 0)
                        if transaction_model.status == Status.CLOSE
                        else (0, -usdt_value)
                    )
                    trust += usdt_value * inbound_fee // total_fee_sum
                    fiat_profit += (
                            transaction_model.amount * inbound_fee // total_fee_sum
                    )
                else:
                    trust += usdt_value * inbound_fee // total_fee_sum

                print(
                    user_id, trust, locked, profit, fiat_trust, fiat_locked, fiat_profit
                )
            balances_changes.append(
                {
                    "transaction_id": transaction_id,
                    "user_id": user_id,
                    "balance_id": balance_id,
                    "profit_balance": profit,
                    "trust_balance": trust,
                    "locked_balance": locked,
                    "fiat_profit_balance": fiat_profit,
                    "fiat_trust_balance": fiat_trust,
                    "fiat_locked_balance": fiat_locked,
                }
            )
        if initial_status == Status.PENDING and status in [Status.ACCEPT, Status.CLOSE]:
            stmt_count = (
                update(BankDetailModel)
                .where(BankDetailModel.id == transaction_model.bank_detail_id,
                    BankDetailModel.pending_count > 0)
                .values(pending_count=BankDetailModel.pending_count - 1)
            )
            await session.execute(stmt_count)
            stmt_count2 = (
                update(TeamModel)
                .where(TeamModel.id == transaction_model.team_id,
                       TeamModel.count_pending_inbound > 0)
                .values(count_pending_inbound=TeamModel.count_pending_inbound - 1)
            )
            await session.execute(stmt_count2)
            if status == Status.ACCEPT:
                stmt_active = (
                    update(BankDetailModel)
                    .where(BankDetailModel.id == transaction_model.bank_detail_id,
                           BankDetailModel.auto_managed == True)
                    .values(is_auto_active=False)
                )

                if from_device:
                    await session.execute(
                        update(BankDetailModel)
                        .where(BankDetailModel.id == transaction_model.bank_detail_id)
                        .values(need_check_automation=False)
                    )

                await session.execute(stmt_active)
                stmt_limits = (
                    update(BankDetailModel)
                    .where(BankDetailModel.id == transaction_model.bank_detail_id)
                    .values(
                        today_transactions_count=case(
                            (
                                func.date(BankDetailModel.last_transaction_timestamp) < func.date(func.now()),
                                1
                            ),
                            else_=BankDetailModel.today_transactions_count + 1
                        ),
                        last_transaction_timestamp=func.now(),
                        last_accept_timestamp=func.now()
                    )
                )
                await session.execute(stmt_limits)
        if initial_status == Status.ACCEPT and status == Status.CLOSE:
            #print(BankDetailModel.today_amount_used, (transaction_model.amount // DECIMALS))
            #(transaction_model.amount // DECIMALS) - отрицательный
            stmt = (
                update(BankDetailModel)
                .where(BankDetailModel.id == transaction_model.bank_detail_id)
                .values(
                    today_transactions_count=case(
                            (
                                BankDetailModel.today_transactions_count > 0,
                                BankDetailModel.today_transactions_count - 1
                            ),
                            else_=0
                    ),
                    today_amount_used=case(
                        (BankDetailModel.today_amount_used < -(transaction_model.amount // DECIMALS),
                        0),
                        else_=BankDetailModel.today_amount_used + (transaction_model.amount // DECIMALS)
                    )
                )
            )
            await session.execute(stmt)
        if initial_status == Status.CLOSE and status == Status.ACCEPT:
            stmt = (
                update(BankDetailModel)
                .where(BankDetailModel.id == transaction_model.bank_detail_id)
                .values(
                    today_transactions_count=case(
                        (
                            func.date(BankDetailModel.last_transaction_timestamp) < func.current_date(),
                            1
                        ),
                        else_=BankDetailModel.today_transactions_count + 1
                    ),
                    today_amount_used=case(
                        (func.date(BankDetailModel.last_transaction_timestamp) < func.date(func.now()),
                         transaction_model.amount // DECIMALS),
                        else_=BankDetailModel.today_amount_used + (transaction_model.amount // DECIMALS)
                    )
                )
            )
            await session.execute(stmt)

    if transaction_model.direction == Direction.OUTBOUND:
        for outbound_fee, user_id, balance_id in update_user_balances_list:
            profit = 0
            trust = 0
            locked = 0

            fiat_profit = 0
            fiat_trust = 0
            fiat_locked = 0

            if transaction_model.economic_model == EconomicModel.CRYPTO:
                if user_id == transaction_model.team_id:
                    profit = outbound_fee * usdt_value // total_fee_sum
                    trust = usdt_value
                elif user_id == transaction_model.merchant_id:
                    if transaction_model.status != Status.CLOSE:
                        trust = (
                                -usdt_value
                                * (total_fee_sum - outbound_fee)
                                // total_fee_sum
                        )
                        locked = -usdt_value
                    else:
                        trust = (
                                -usdt_value
                                - usdt_value
                                * (total_fee_sum - outbound_fee)
                                // total_fee_sum
                        )
                    merchant_trust_change = trust + locked
                else:
                    profit = outbound_fee * usdt_value // total_fee_sum

            elif transaction_model.economic_model == EconomicModel.FIAT:
                if user_id == transaction_model.team_id:
                    fiat_profit = (
                            outbound_fee * transaction_model.amount // total_fee_sum
                    )
                    fiat_trust = transaction_model.amount
                    fiat_trust += fiat_profit
                elif user_id == transaction_model.merchant_id:
                    fiat_trust -= (
                            transaction_model.amount
                            * (total_fee_sum - outbound_fee)
                            // total_fee_sum
                    )
                    if transaction_model.status != Status.CLOSE:
                        fiat_locked -= transaction_model.amount
                    else:
                        fiat_trust -= transaction_model.amount
                else:
                    fiat_profit = (
                            outbound_fee * transaction_model.amount // total_fee_sum
                    )

            elif transaction_model.economic_model == EconomicModel.FIAT_CRYPTO_PROFIT:
                if user_id == transaction_model.team_id:
                    fiat_profit = (
                            outbound_fee * transaction_model.amount // total_fee_sum
                    )
                    fiat_trust = (
                            transaction_model.amount
                            * (total_fee_sum + agents_fee_sum)
                            // total_fee_sum
                    )
                    fiat_trust += fiat_profit
                    trust = -usdt_value * agents_fee_sum // total_fee_sum
                elif user_id == transaction_model.merchant_id:
                    fiat_trust -= (
                            transaction_model.amount
                            * (total_fee_sum - outbound_fee)
                            // total_fee_sum
                    )
                    if transaction_model.status != Status.CLOSE:
                        fiat_locked -= transaction_model.amount
                    else:
                        fiat_trust -= transaction_model.amount
                else:
                    profit = outbound_fee * usdt_value // total_fee_sum

            if transaction_model.economic_model == EconomicModel.CRYPTO_FIAT_PROFIT:
                if user_id == transaction_model.team_id:
                    trust = usdt_value + outbound_fee * usdt_value // total_fee_sum
                elif user_id == transaction_model.merchant_id:
                    if transaction_model.status != Status.CLOSE:
                        trust = (
                                -usdt_value
                                * (total_fee_sum - outbound_fee)
                                // total_fee_sum
                        )
                        locked = -usdt_value

                        fiat_trust = (
                                -transaction_model.amount
                                * (total_fee_sum - outbound_fee)
                                // total_fee_sum
                        )
                        fiat_locked = -transaction_model.amount
                    else:
                        trust = (
                                -usdt_value
                                - usdt_value
                                * (total_fee_sum - outbound_fee)
                                // total_fee_sum
                        )
                        fiat_trust = (
                                -transaction_model.amount
                                - transaction_model.amount
                                * (total_fee_sum - outbound_fee)
                                // total_fee_sum
                        )
                    merchant_trust_change = trust + locked
                else:
                    trust += outbound_fee * usdt_value // total_fee_sum

            balances_changes.append(
                {
                    "transaction_id": transaction_id,
                    "user_id": user_id,
                    "balance_id": balance_id,
                    "profit_balance": profit,
                    "trust_balance": trust,
                    "locked_balance": locked,
                    "fiat_profit_balance": fiat_profit,
                    "fiat_trust_balance": fiat_trust,
                    "fiat_locked_balance": fiat_locked,
                }
            )

    await add_balance_changes(session=session, changes=balances_changes)
    transaction_model.status = status
    create_timestamp = transaction_model.create_timestamp
    delta_seconds = (FUTURE_DATE - create_timestamp).total_seconds()
    transaction_model.priority = int(delta_seconds)

    if is_change_sum_on_inbound_accepted:
        transaction_model.amount = final_amount_on_inbound_accepted
    if initial_status in (Status.PENDING, Status.PROCESSING, Status.OPEN) and status in (Status.CLOSE, Status.ACCEPT):
        transaction_model.final_status_timestamp = datetime.utcnow()

    if initial_status != Status.ACCEPT and status == Status.ACCEPT:
        await session.execute(
            update(AppealModel)
            .where(AppealModel.transaction_id == transaction_model.id)
            .values(close_timestamp=func.now())
        )

    await session.commit()

    async def after_trx_creation_task():
        logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task ENTER")
        try:
            logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:parallel_session ENTER")
            async with async_session() as parallel_session:
                # await get_balances(
                #     user_id=transaction_model.merchant_id,
                #     session=parallel_session,
                # )
                # await get_balances(
                #     user_id=transaction_model.team_id,
                #     session=parallel_session,
                # )
                if transaction_model.direction == Direction.INBOUND and \
                        status == Status.ACCEPT and initial_status in (Status.PENDING, Status.PROCESSING, Status.CLOSE):
                    await parallel_session.execute(
                        update(BankDetailModel)
                        .values(
                            {
                                BankDetailModel.amount_used:
                                    BankDetailModel.amount_used + transaction_model.amount
                            }
                        )
                        .filter(transaction_model.bank_detail_id == BankDetailModel.id)
                    )
                if transaction_model.direction == Direction.INBOUND and \
                        initial_status in (Status.PENDING, Status.CLOSE) and status == Status.ACCEPT:
                    stmt = text("""
                            UPDATE vip_payer_model AS vpm
                            SET last_accept_timestamp = 
                                CASE
                                    WHEN :initial_status = 'close' THEN GREATEST(:final_status_ts, vpm.last_accept_timestamp)
                                    ELSE GREATEST(NOW(), vpm.last_accept_timestamp)
                                END
                            FROM bank_detail_model AS bdm
                            WHERE 
                                vpm.payer_id = :payer_id
                                AND vpm.bank_detail_id = bdm.profile_id
                                AND bdm.id = :bank_detail_id
                        """)

                    await parallel_session.execute(stmt, {
                        "initial_status": initial_status,
                        "final_status_ts": transaction_model.final_status_timestamp,
                        "payer_id": transaction_model.merchant_payer_id,
                        "merchant_id": transaction_model.merchant_id,
                        "bank_detail_id": transaction_model.bank_detail_id
                    })

                await parallel_session.commit()

            logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:parallel_session EXIT")
        except Exception as e:
            logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:parallel_session:exception, {e}")
        try:
            logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:merchant_callback ENTER")
            await merchant_callback(
                hook_uri=transaction_model.hook_uri,
                direction=transaction_model.direction,
                merchant_id=transaction_model.merchant_id,
                transaction_id=transaction_model.id,
                amount=transaction_model.amount,
                status=transaction_model.status,
                merchant_transaction_id=transaction_model.merchant_transaction_id,
                request_id=request_id,
                merchant_trust_change=merchant_trust_change,
                currency_id=transaction_model.currency_id,
                exchange_rate=transaction_model.exchange_rate
            )
            logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:merchant_callback EXIT")
        except Exception as e:
            logger.info(
                f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:merchant_callback:exception, {e}")

    logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:future ENTER")
    asyncio.ensure_future(after_trx_creation_task())
    logger.info(f"[TrackingLog] - transaction_id = {transaction_model.id}, after_trx_creation_task:future EXIT")
    return ETs.Response(**transaction_model.__dict__)


async def get_fields_for_update_response(
        response_update: ETs.Response, role
) -> ETs.Response:
    async with ro_async_session() as session:
        UserModel_merchant = aliased(UserModel, name="UserModel_merchant")
        UserModel_team = aliased(UserModel, name="UserModel_team")

        query = (
            select(
                ExternalTransactionModel,
                MerchantModel.name.label("merchant_name"),
                case(
                    (ExternalTransactionModel.team_id.is_(None), None),
                    else_=TeamModel.name
                ).label("team_name"),
                MerchantModel.transaction_auto_close_time_s,
                MerchantModel.transaction_outbound_auto_close_time_s,
                MessageModel.text,
                TagModel.code.label("tag_code")
            )
            .distinct()
            .outerjoin(
                TeamModel,
                TeamModel.id == ExternalTransactionModel.team_id,
            )
            .join(
                MerchantModel,
                MerchantModel.id == ExternalTransactionModel.merchant_id,
            ).outerjoin(
                MessageModel,
                MessageModel.external_transaction_id == ExternalTransactionModel.id
            ).join(
                TagModel, TagModel.id == ExternalTransactionModel.tag_id
            )
            .filter(
                ExternalTransactionModel.id == response_update.id
            )
        )
        trx_list = await session.execute(query)
        result = [ETs.Response(
            **i[0].__dict__,
            merchant_name=i[1] if role == Role.SUPPORT else None,
            team_name=i[2] if role == Role.SUPPORT else None,
            transaction_auto_close_time_s=i[3],
            transaction_outbound_auto_close_time_s=i[4],
            text=i[5],
            tag_code=i[6] if role == Role.SUPPORT or role == Role.MERCHANT else None
        ) for i in trx_list]
        return result[0]


async def external_transaction_update(
        request_update_status: ETs.RequestUpdateStatusDB,
) -> ETs.Response:
    async with async_session() as session:
        if request_update_status.status in (Status.ACCEPT, Status.CLOSE):
            return await external_transaction_update_(
                merchant_transaction_id=request_update_status.merchant_transaction_id,
                transaction_id=request_update_status.transaction_id,
                reason=request_update_status.reason,
                session=session,
                new_amount=request_update_status.new_amount,
                status=request_update_status.status,
                final_status=request_update_status.final_status
            )
        else:
            raise exceptions.ExternalTransactionRequestStatusException(
                statuses=[Status.ACCEPT, Status.CLOSE]
            )


async def external_transaction_transfer(
        transaction_id: str,
        team_id: str,
) -> ETs.Response:
    async with async_session() as session:
        transaction_model: ExternalTransactionModel = (
            await _find_external_transaction_by_id(
                transaction_id=transaction_id,
                session=session,
            )
        )

        if transaction_model.status in (Status.ACCEPT, Status.PROCESSING, Status.CLOSE):
            raise exceptions.UnableToTransferTransactionException()

        #         next_team_id_q = await session.execute(text(
        #             f"""
        # SELECT u.id
        # FROM user_model u
        # INNER JOIN user_balance_change_nonce_model n
        # ON u.id = n.user_id
        # INNER JOIN traffic_weight_contact_model f
        # ON f.team_id = u.id AND merchant_id = '{transaction_model.merchant_id}'
        # WHERE u.is_outbound_enabled = TRUE
        # AND u.role = '{Role.TEAM}'
        # AND f.outbound_traffic_weight > 0
        # AND n.trust_balance <= (SELECT trust_balance
        #                           FROM user_balance_change_nonce_model n
        #                           WHERE n.user_id = '{team_id}' LIMIT 1)
        # AND u.id != '{team_id}'
        # ORDER BY n.trust_balance DESC, u.id LIMIT 1;
        #             """))
        #         next_team_id = next_team_id_q.scalars().first()
        #         if next_team_id is None:
        #             next_team_id_q = await session.execute(text(
        #                 f"""
        # SELECT u.id
        # FROM user_model u
        # INNER JOIN user_balance_change_nonce_model n
        # ON u.id = n.user_id
        # INNER JOIN traffic_weight_contact_model f
        # ON f.team_id = u.id AND merchant_id = '{transaction_model.merchant_id}'
        # WHERE u.is_outbound_enabled = TRUE
        # AND u.role = '{Role.TEAM}'
        # AND f.outbound_traffic_weight > 0
        # AND u.id != '{team_id}'
        # ORDER BY n.trust_balance DESC , u.id LIMIT 1;
        #             """))
        #             next_team_id = next_team_id_q.scalars().first()
        #             if next_team_id is None:
        #                 raise exceptions.UnableToTransferTransactionException()
        await session.execute(
            update(TeamModel)
            .where(TeamModel.id == transaction_model.team_id)
            .values(
                today_outbound_amount_used=case(
                    (func.date(TeamModel.last_transaction_timestamp) < func.date(func.now()),
                     0),
                    else_=TeamModel.today_outbound_amount_used - (transaction_model.amount // DECIMALS)
                ),
            )
        )

        transaction_model.team_id = None
        transaction_model.transfer_to_team_timestamp = None
        transaction_model.count_hold = 0

        stmt = pg_insert(TransferAssociationModel).values(
            team_id=team_id,
            transaction_id=transaction_id,
            transfer_from_team_timestamp=datetime.utcnow()
        ).on_conflict_do_update(
            index_elements=["team_id", "transaction_id"],
            set_={
                "transfer_from_team_timestamp": datetime.utcnow()
            }
        )

        await session.execute(stmt)

        name_q = await session.execute(
            select(UserModel.name).where(UserModel.id == team_id)
        )

        team_name = name_q.scalar()
        request_id = str(uuid.uuid4())
        log_data = TransferOutboundTransactionLogSchema(
            request_id=request_id,
            team_name=team_name,
            team_id=team_id,
            transaction_id=transaction_id
        )

        logger.info(log_data.model_dump_json())
        logger.info(f"[TransferOutboundTransaction] - team_name = {team_name}, team_id = {team_id}, transaction_id = {transaction_id}, UTC_time = {datetime.utcnow()}")

        await session.commit()

        return ETs.Response(**transaction_model.__dict__)


async def transfer_pay_out_to_team(
    transaction_id: str,
    data: ETs.RequestTransferToTeam
) -> ETs.Response:
    # TODO: refactor (create exceptions, join team and merchant in find transaction)
    async with async_session() as session:
        # TODO: validate get external transaction with namespace for support

        transaction: ExternalTransactionModel = (
            await _find_external_transaction_by_id(
                transaction_id=transaction_id,
                session=session
            )
        )

        if transaction.team_id is not None:
            raise exceptions.BadRequestException("Transaction is already taken by another team")
        
        if transaction.direction != Direction.OUTBOUND:
            raise exceptions.BadRequestException("Transfer works only for outbound transactions")

        team = (await session.execute(
            select(TeamModel)
            .where(TeamModel.id == data.team_id)
        )).scalar_one_or_none()

        if not team:
            raise exceptions.TeamNotFoundException()
        
        merchant = (await session.execute(
            select(MerchantModel)
            .where(MerchantModel.id == transaction.merchant_id)
        )).scalar_one_or_none()

        if not merchant:
            raise exceptions.InternalServerErrorException()
        
        if merchant.geo_id != team.geo_id:
            raise exceptions.BadRequestException("Can't transfer to team from another geo")
        
        transaction.transfer_to_team_timestamp = func.now()
        transaction.team_id = team.id
        transaction.count_hold = 0

        await session.commit()

        logger.info(f"[TransferOutboundToTeam] - transaction_id = {transaction_id}, team_id = {team.id}, UTC_time = {datetime.utcnow()}")

        return ETs.Response(**transaction.__dict__)


async def return_transaction_to_pool(transaction_id) -> ETs.Response:
    async with async_session() as session:
        transaction: ExternalTransactionModel = (
            await _find_external_transaction_by_id(
                transaction_id=transaction_id,
                session=session
            )
        )

        if transaction.status != Status.PROCESSING:
            raise exceptions.BadRequestException("Return works only for transactions with processing status")
        
        if transaction.direction != Direction.OUTBOUND:
            raise exceptions.BadRequestException("Return works only for outbound transactions")
        
        transaction.team_id = None
        transaction.transfer_to_team_timestamp = None
        transaction.count_hold = 0
        transaction.status = Status.PENDING
        transaction.file_uri = None

        await session.commit()

        logger.info(f"[ReturnOutboundToPool] - transaction_id = {transaction_id}, UTC_time = {datetime.utcnow()}")

        return ETs.Response(**transaction.__dict__)


async def _find_external_transaction_by_id(
        session: AsyncSession,
        transaction_id: str | None = None,
        merchant_transaction_id: str | None = None,
) -> ExternalTransactionModel:
    if transaction_id is not None:
        block_res = await session.execute(
            select(ExternalTransactionModel)
            .filter(
                ExternalTransactionModel.id == transaction_id
            ).with_for_update()
        )
        block_res = block_res.scalars().first()
        if block_res is None:
            raise exceptions.ExternalTransactionNotFoundException()
        logger.info(f'find:{transaction_id}:{block_res.status}')
        contract_req = await session.execute(
            select(ExternalTransactionModel)
            .filter(
                ExternalTransactionModel.id == transaction_id
            )
        )
    else:
        block_res = await session.execute(
            select(ExternalTransactionModel)
            .filter(
                ExternalTransactionModel.merchant_transaction_id == merchant_transaction_id
            )
            .with_for_update()
        )
        block_res = block_res.scalars().first()
        if block_res is None:
            raise exceptions.ExternalTransactionNotFoundException()
        logger.info(f'find:{transaction_id}:{block_res.status}')
        contract_req = await session.execute(
            select(ExternalTransactionModel)
            .filter(
                ExternalTransactionModel.merchant_transaction_id == merchant_transaction_id
            )
        )
    result = contract_req.scalars().first()
    if result is None:
        raise exceptions.ExternalTransactionNotFoundException()
    logger.info(f'find:{transaction_id}:{result.status}')
    return result


async def external_transaction_update_file_reason(
    transaction_id: str,
    files: List[ETs.FileBase64],
    current_user: UserTeamScheme
):
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        transaction_model = await _find_external_transaction_by_id(
            transaction_id=transaction_id,
            session=session,
        )

        if transaction_model.status == Status.ACCEPT:
            raise exceptions.ExternalTransactionExistingStatusException(
                statuses=[Status.PENDING, Status.PROCESSING, Status.CLOSE]
            )

        if transaction_model.direction != Direction.OUTBOUND:
            raise exceptions.ExternalTransactionExistingDirectionException(
                directions=[Direction.OUTBOUND]
            )
        buffers = await clone_base64_files(files)
        if len(buffers) >= 2:
            merged_pdf = await tg.merge_files_to_pdf(buffers)
            first_filename = buffers[0][0]
            if not first_filename.lower().endswith(".pdf"):
                first_filename = first_filename.rsplit(".", 1)[0] + ".pdf"
            merged_pdf.seek(0)
            file_save_path = await file_storage.upload_file(
                merged_pdf, filename=first_filename
            )
        else:
            filename, buffer = buffers[0]
            buffer.seek(0)
            file_save_path = await file_storage.upload_file(
                buffer, filename=filename
            )
        transaction_model.file_uri = file_save_path
        await session.commit()
        log_data = CancelOutboundWithReasonLogSchema(
            request_id=request_id,
            team_name=current_user.name,
            team_id=current_user.id,
            transaction_id=transaction_id,
            reason=transaction_model.reason
        )

        logger.info(log_data.model_dump_json())
        logger.info(f"[CancelOutboundWithReason] - team_name = {current_user.name}, team_id = {current_user.id}, transaction_id = {transaction_id}, reason = {transaction_model.reason}, UTC_time = {datetime.utcnow()}")


async def clone_upload_files(files: list[UploadFile]) -> list[tuple[str, BytesIO]]:
    result = []
    for f in files:
        content = await f.read()
        buf = BytesIO(content)
        buf.seek(0)
        result.append((f.filename, buf))
    return result

async def clone_base64_files(files: List[ETs.FileBase64]) -> list[tuple[str, BytesIO]]:
    result = []
    for f in files:
        content = base64.b64decode(f.file)
        buf = BytesIO(content)
        buf.seek(0)
        result.append((f.name, buf))
    return result


def get_normalized_file_hash(content: bytes, filename: str) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1]
    try:
        if suffix == "pdf":
            reader = PdfReader(BytesIO(content))
            full_text = "\n".join((page.extract_text() or "").strip() for page in reader.pages)
            normalized = full_text.replace("\r\n", "\n").replace("\r", "\n").strip()
            return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        # elif suffix in ("jpg", "jpeg", "png"):
        #     img = Image.open(BytesIO(content))
        #     buf = BytesIO()
        #     img.save(buf, format=img.format)
        #     return hashlib.sha256(buf.getvalue()).hexdigest()

    except Exception as e:
        logger.info(f"[HashError] - exception when get hash file: {e}")

    return "no hash"


async def external_transaction_update_file_and_send_to_tg(
        request_update_file: ETs.RequestUpdateFileDB,
        current_user: UserTeamScheme,
        files: List[UploadFile],
) -> ETs.Response:
    request_id = str(uuid.uuid4())
    file_hashes_to_save = []
    
    for file in files:
        content = await file.read()
        file.file.seek(0)
        file_hash = get_normalized_file_hash(content, file.filename)
        if file_hash == "no hash":
            continue
        key = f"file_hash:{file_hash}"
        value = request_update_file.transaction_id

        existing = await redis.rediss.get(key)
        if existing:
            existing = existing.decode()
            if existing != request_update_file.transaction_id:
                raise exceptions.AlreadyUsedHashException(file.filename)

        file_hashes_to_save.append((key, value))
    
    for key, value in file_hashes_to_save:
        await redis.rediss.set(key, value, ex=30 * 24 * 60 * 60)
    
    async with async_session() as session:
        transaction_model = await _find_external_transaction_by_id(
            transaction_id=request_update_file.transaction_id,
            session=session,
        )

        if transaction_model.status != Status.PENDING and transaction_model.status != Status.PROCESSING:
            raise exceptions.ExternalTransactionExistingStatusException(
                statuses=[Status.PENDING]
            )

        if transaction_model.direction != Direction.OUTBOUND:
            raise exceptions.ExternalTransactionExistingDirectionException(
                directions=[Direction.OUTBOUND]
            )

        if transaction_model.status == Status.CLOSE:
            await _change_trust_locked_balances(
                session, transaction_model, is_add_locked=True
            )

        transaction_model.file_uri = request_update_file.file_uri
        transaction_model.status = Status.PROCESSING
        create_timestamp = transaction_model.create_timestamp
        delta_seconds = (FUTURE_DATE - create_timestamp).total_seconds()
        transaction_model.priority = int(delta_seconds)

        # TODO: create function to get telegram_bot_secret and telegram_verifier_chat_id by user.namespace.id
        telegram_bot_secret = (await session.execute(
            select(NamespaceModel.telegram_bot_secret)
            .where(NamespaceModel.id == current_user.namespace.id)
        )).scalar_one_or_none()

        # TODO: replace -> take geo_id from transaction_model.team.geo_id
        team = (await session.execute(
            select(TeamModel)
            .where(TeamModel.id == transaction_model.team_id)
        )).scalar_one_or_none()

        telegram_verifier_chat_id = (await session.execute(
            select(TelegramVerifierChatIdModel.chat_id)
            .where(
                TelegramVerifierChatIdModel.namespace_id == current_user.namespace.id,
                TelegramVerifierChatIdModel.geo_id == team.geo_id
            )
        )).scalar_one_or_none()

        raw = str(transaction_model.bank_detail_number).replace('_', ' ').strip()

        digits_only = ''.join(filter(str.isdigit, raw))

        if len(digits_only) == 11 and digits_only.startswith(('7', '8')):
            normalized = '7' + digits_only[1:]
            formatted = f'{normalized[0]} {normalized[1:4]} {normalized[4:7]} {normalized[7:9]} {normalized[9:11]}'
        elif len(raw) == 16 and raw.isdigit():
            formatted = ' '.join([raw[i:i + 4] for i in range(0, 16, 4)])
        else:
            formatted = raw

        # -------------TELEGRAM-----------------------------------------------------------------------------------------
        tag = " #мультичек" if len(files) > 1 else ""
        message: str = f"""
            #outbound{tag}
trans\_id               `{transaction_model.id}`
team name         `{team.name}`
team\_id               `{transaction_model.team_id}`
date                     {transaction_model.create_timestamp.strftime("%Y.%m.%d %H:%M:%S")}
number               *{formatted}*
bank                    {str(transaction_model.bank_detail_bank).replace('_', ' ')}
client name        {str(transaction_model.bank_detail_name).replace('_', ' ')}
amount               {transaction_model.amount // DECIMALS} {transaction_model.currency_id}
            """
        message_for_multi: str = f"""
             #outbound {tag} #продолжение
trans\_id               `{transaction_model.id}`
        """
        accept = f"accept|{transaction_model.id}"
        decline = f"close|{transaction_model.team_id}"
        print(base64.b64encode(decline.encode()).decode())
        buffers = await clone_upload_files(files)

        async def save_file(buffers: list[tuple[str, BytesIO]]):
            if len(buffers) >= 2:
                file = await tg.merge_files_to_pdf(buffers)
                first_filename = buffers[0][0]
                if not first_filename.lower().endswith(".pdf"):
                    first_filename = first_filename.rsplit(".", 1)[0] + ".pdf"
                file.seek(0)
                file_save_path = await file_storage.upload_file(
                    file, filename=first_filename
                )
            else:
                filename, buffer = buffers[0]
                buffer.seek(0)
                file_save_path = await file_storage.upload_file(
                    buffer, filename=filename
                )
            transaction_model.file_uri = file_save_path

        if telegram_bot_secret is not None and telegram_verifier_chat_id is not None:
            await asyncio.gather(
                tg.send_to_chat(
                    api_secret=telegram_bot_secret,
                    chat_id=telegram_verifier_chat_id,
                    message=message,
                    message_for_multi=message_for_multi,
                    decline_callback=decline,
                    accept_callback=accept,
                    files=buffers,
                ),
                save_file(buffers),
            )

        # --------------------------------------------------------------------------------------------------------------
        await session.commit()
        log_data = UpdatePayOutTransactionLogSchema(
            request_id=request_id,
            team_name=team.name,
            team_id=team.id,
            transaction_id=transaction_model.id,
            status=transaction_model.status
        )

        logger.info(log_data.model_dump_json())
        logger.info(
            f"[UpdatePayOutTransaction] - team_name = {team.name}, transaction_id = {transaction_model.id}, status = {transaction_model.status}, UTC_time = {datetime.utcnow()}")
        return ETs.Response(
            **transaction_model.__dict__,
        )


async def check_device_token(
        request: ETs.RequestCheckDeviceToken,
) -> ETs.ResponseCheckDeviceToken:
    async with ro_async_session() as session:
        team_name = (await session.execute(
            select(TeamModel.name)
            .where(TeamModel.api_secret == request.api_secret)
        )).scalar_one_or_none()

        if team_name is None:
            raise exceptions.UserNotFoundException

        return ETs.ResponseCheckDeviceToken(team_name=team_name)


async def save_message_to_db(
        session, request: ETs.RequestUpdateFromDeviceDB, request_id, close = False
):
    """Сохраняет сообщение в MessageModel, даже если транзакция не найдена."""
    if request.timestamp is None:
        message = await session.execute(
            select(MessageModel).filter(
                MessageModel.text == request.message,
                MessageModel.create_timestamp
                > func.now() - timedelta(seconds=Limit.MESSAGE_BACK_TIME_S),
            )
        )
    else:
        message = await session.execute(
            select(MessageModel).filter(
                MessageModel.text == request.message,
                MessageModel.create_timestamp
                > datetime.utcfromtimestamp(request.timestamp)
                - timedelta(seconds=Limit.MESSAGE_BACK_TIME_S),
            )
        )
    message = message.scalars().first()
    if message is not None:
        return

    user_q = await session.execute(
        select(BankDetailModel.team_id).filter(BankDetailModel.device_hash == request.device_hash)
    )
    user_id = user_q.scalars().first()

    await session.execute(
        insert(MessageModel).values(
            text=request.message,
            user_id=user_id,
            title=request.bank,
            number=request.package_name,
            device_hash=request.device_hash,
            create_timestamp=datetime.utcfromtimestamp(request.timestamp) if request.timestamp else datetime.utcnow(),
            comment='BlockedDetail' if close else None
        )
    )
    if close:
        query = text("""
                UPDATE bank_detail_model
                SET is_active = FALSE, update_timestamp = NOW()
                WHERE device_hash = :device_hash AND is_active = TRUE AND bank = :bank
                RETURNING id, number;
            """)
        result = await session.execute(query, {
            'device_hash': request.device_hash,
            'bank': request.bank
        })
        rows = result.fetchall()
        for row in rows:
            log_data = BlockedDetailLogSchema(
                request_id=request_id,
                id=row.id,
                number=row.number,
                team_id=user_id,
                bank=request.bank,
                device_hash=request.device_hash
            )

            logger.info(log_data.model_dump_json())
            logger.info(f"[BlockedDetail] - id = {row.id}, number = {row.number}, team_id = {user_id}, bank = {request.bank}, device_hash = {request.device_hash}")
            await send_notification(ReqBlockedNotificationSchema(
                team_id=user_id,
                data=ReqDisabledNotificationDataSchema(
                    number=row.number
                )
            ))
    await session.commit()


def log_exceptions_and_requests(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request', None) or (args[0] if args else None)
        logger.info(f"Calling {func.__name__} with request: {request.__dict__}")

        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_message = f"Error in {func.__name__} with request: {request.__dict__}, error: {str(e)}"
            logger.info(error_message)
            raise

    return wrapper


@log_exceptions_and_requests
async def external_transaction_update_from_device(
        request: ETs.RequestUpdateFromDeviceDB,
) -> ETs.Response:
    request.message = preprocess_message(request.message)
    request_id = str(uuid.uuid4())
    if request.timestamp is not None and abs(
            datetime.utcnow() - datetime.utcfromtimestamp(request.timestamp)
    ) < timedelta(minutes=1):
        request.timestamp = None
    header = request.bank
    request.bank = device.get_bank_by_sender(request.bank, request.message, request.package_name)
    msg = str(header).lower()
    if request.package_name is not None:
        request.package_name = str(request.package_name).lower()
    if not (request.package_name is not None and 'messag' not in request.package_name):
        request.package_name = msg
    try:
        # print("device event:", request.api_secret, request.__dict__, end=' ')
        amount, bank_detail_digits, new_amount = device.parse_message(request.message, header, request.bank)
        log_data = ParseMessageLogSchema(
            request_id=request_id,
            api_secret=request.api_secret,
            request=request.__dict__,
            parsed_amount=amount,
            parsed_new_amount=new_amount,
            parsed_bank=request.bank,
            parsed_digits=bank_detail_digits,
            title=header,
        )

        logger.info(log_data.model_dump_json())
        logger.info(
            f"[PARSE MESSAGE]\n"
            f"api_secret: {request.api_secret}\n"
            f"request: {request.__dict__}\n"
            f"parsed_amount: {amount}\n"
            f"parsed_new_amount: {new_amount}\n"
            f"parsed_bank: {request.bank}\n"
            f"parsed_digits: {bank_detail_digits}\n"
            f"title: {header}\n"
        )
    except exceptions.BlockedCardException:
        if request.bank is not None:
            async with async_session() as session:
                await save_message_to_db(session, request, request_id, close=True)
        raise exceptions.BlockedCardException()
    except ValueError:
        if request.bank is not None:
            async with async_session() as session:
                await save_message_to_db(session, request, request_id)
        raise exceptions.ExternalTransactionCannotParseAmount()

    if amount is None:
        if request.bank is not None:
            async with async_session() as session:
                await save_message_to_db(session, request, request_id)
        raise exceptions.ExternalTransactionCannotParseAmount()

    async with async_session() as session:
        if request.timestamp is None:
            message = await session.execute(
                select(MessageModel).filter(
                    MessageModel.text == request.message,
                    MessageModel.create_timestamp
                    > func.now() - timedelta(seconds=Limit.MESSAGE_BACK_TIME_S),
                )
            )
        else:
            message = await session.execute(
                select(MessageModel).filter(
                    MessageModel.text == request.message,
                    MessageModel.create_timestamp
                    > datetime.utcfromtimestamp(request.timestamp)
                    - timedelta(seconds=Limit.MESSAGE_BACK_TIME_S),
                )
            )
        message = message.scalars().first()
        if message is not None:
            raise exceptions.ExternalTransactionMessageRepeatedException()
        team_q = await session.execute(
            select(TeamModel.id).filter(TeamModel.api_secret == request.api_secret)
        )
        team_id = team_q.scalars().first()
        if team_id is None:
            if request.bank is not None:
                await save_message_to_db(session, request, request_id)
            raise exceptions.UserNotFoundException()
        if request.timestamp is None:
            query = select(
                ExternalTransactionModel.id,
                ExternalTransactionModel.team_id,
                ExternalTransactionModel.bank_detail_number,
                BankDetailModel.device_hash,
                BankDetailModel.bank,
                BankDetailModel.type,
            ).filter(
                BankDetailModel.id == ExternalTransactionModel.bank_detail_id,
                ExternalTransactionModel.status == Status.PENDING,
                ExternalTransactionModel.team_id == team_id,
                ExternalTransactionModel.direction == Direction.INBOUND,
                ExternalTransactionModel.amount == amount,
            )
        else:
            query = select(
                ExternalTransactionModel.id,
                ExternalTransactionModel.team_id,
                ExternalTransactionModel.bank_detail_number,
                BankDetailModel.device_hash,
                BankDetailModel.bank,
                BankDetailModel.type,
            ).join(MerchantModel, MerchantModel.id == ExternalTransactionModel.merchant_id).filter(
                BankDetailModel.id == ExternalTransactionModel.bank_detail_id,
                ExternalTransactionModel.status.in_((Status.PENDING, Status.CLOSE)),
                ExternalTransactionModel.team_id == team_id,
                ExternalTransactionModel.direction == Direction.INBOUND,
                ExternalTransactionModel.amount == amount,
                ExternalTransactionModel.create_timestamp
                + func.make_interval(0, 0, 0, 0, 0, 0, MerchantModel.transaction_auto_close_time_s)
                > datetime.utcfromtimestamp(request.timestamp),
                ExternalTransactionModel.create_timestamp <= datetime.utcfromtimestamp(request.timestamp),
            )
        transactions_q = await session.execute(query)
        transaction_list = transactions_q.all()
        initial_count = len(transaction_list)
        if bank_detail_digits:
            query = query.filter(BankDetailModel.comment == bank_detail_digits)
            transactions_q = await session.execute(query)
            transaction_list = transactions_q.all()
            filtered_count = len(transaction_list)
            if filtered_count == 0 and initial_count > 0:
                if request.bank is not None:
                    await save_message_to_db(session, request, request_id)
                raise exceptions.ExternalTransactionDetailCommentException(comment=bank_detail_digits)
        candidates: list[Tuple[int, str, str]] = []
        for (
                t_id,
                t_team_id,
                t_bank_detail,
                device_hash,
                bank,
                d_type
        ) in transaction_list:
            score = 0
            if request.device_hash is not None and device_hash == request.device_hash:
                score -= 8
            if request.device_hash is not None and device_hash != request.device_hash:
                score += 32
            if request.bank != bank:
                score += 32
            if bank != request.bank:
                score += 1
            if (
                    bank_detail_digits is not None
                    and len(t_bank_detail) > 4
                    and bank_detail_digits in t_bank_detail[-4:]
            ):
                score -= 16
            if d_type == Type.PHONE:
                score -= 8
            candidates.append((score, t_id, t_team_id, bank, t_bank_detail))
        candidates.sort(key=lambda x: x[0])
        if len(candidates) == 0:
            if request.bank is not None:
                await save_message_to_db(session, request, request_id)
            raise exceptions.ExternalTransactionNoCandidatesForAmount()
        if len(candidates) >= 2 and candidates[0][0] == candidates[1][0]:
            if request.bank is not None:
                await save_message_to_db(session, request, request_id)
            raise exceptions.ExternalTransactionAmountCollisionException()
        if bank_detail_digits is not None and candidates[0][0] > -16 and request.bank != 'alfabusiness':
            if request.bank is not None:
                await save_message_to_db(session, request, request_id)
            raise exceptions.ExternalTransactionCardCollisionException()
        if candidates[0][0] > -8:
            if request.bank is not None:
                await save_message_to_db(session, request, request_id)
            raise exceptions.ExternalTransactionCardCollisionException()
        t_id, t_team_id, tr_bank, t_bank_detail = candidates[0][1], candidates[0][2], candidates[0][3], candidates[0][4]
        if request.bank == "alfabank" and tr_bank != "alfabank":
            if request.bank is not None:
                await save_message_to_db(session, request, request_id)
            raise exceptions.ExternalTransactionNoCandidatesForAmount()

        if request.timestamp is None:
            await session.execute(
                insert(MessageModel).values(
                    text=request.message,
                    external_transaction_id=t_id,
                    user_id=team_id,
                    title=request.bank,
                    amount=amount,
                    bank_detail_number=t_bank_detail,
                    number=request.package_name,
                    comment=bank_detail_digits if bank_detail_digits is not None else '',
                    device_hash=request.device_hash
                ))
        else:
            await session.execute(
                insert(MessageModel).values(
                    text=request.message,
                    external_transaction_id=t_id,
                    user_id=team_id,
                    title=request.bank,
                    amount=amount,
                    bank_detail_number=t_bank_detail,
                    number=request.package_name,
                    comment=bank_detail_digits if bank_detail_digits is not None else '',
                    device_hash=request.device_hash,
                    create_timestamp=datetime.utcfromtimestamp(request.timestamp)
                ))

        await session.commit()
        if request.timestamp is None:
            message = await session.execute(
                select(func.count(MessageModel.amount)).filter(
                    MessageModel.amount == amount,
                    MessageModel.device_hash == request.device_hash,
                    MessageModel.comment == bank_detail_digits,
                    MessageModel.user_id == team_id,
                    MessageModel.create_timestamp
                    > func.now()
                    - timedelta(seconds=5)
                )
            )
        else:
            message = await session.execute(
                select(func.count(MessageModel.amount)).filter(
                    MessageModel.amount == amount,
                    MessageModel.device_hash == request.device_hash,
                    MessageModel.comment == bank_detail_digits,
                    MessageModel.user_id == team_id,
                    MessageModel.create_timestamp
                    > datetime.utcfromtimestamp(request.timestamp)
                    - timedelta(seconds=5)
                )
            )

        message = message.scalars().first()
        if message is not None and message >= 2:
            raise exceptions.ExternalTransactionMessageRepeatedException()
        log_data = SuccessUpdateFromDeviceLogSchema(
            request_id=request_id,
            team_id=team_id,
            transaction_id=t_id
        )

        logger.info(log_data.model_dump_json())
        logger.info( f"[SuccessUpdateFromDevice] - team_id = {team_id}, transaction_id = {t_id}, UTC_time = {datetime.utcnow()}")
        result = await external_transaction_update_(
            transaction_id=t_id,
            session=session,
            status=Status.ACCEPT,
            new_amount=new_amount,
            final_status=TransactionFinalStatusEnum.AUTO,
            from_device=True
        )

    return ETs.Response(**result.__dict__)


# -----------------------------------v2----------------------------------------------------------------------------------

async def get_rand_complements(amount, left_eps_change_amount_allowed, right_eps_change_amount_allowed):
    return {amount} | {amount + i * DECIMALS for i in range(left_eps_change_amount_allowed, right_eps_change_amount_allowed + 1)}


async def h2h_create_inbound(
        request: v2_ETs.H2HCreateInbound,
        req: Request,
        id: Optional[str] = None
):
    #if request.merchant_id == "3cdd12cb-e46f-4b79-ab4a-47b62c52fe35" and request.amount >= 100000 * DECIMALS:
    #    raise exceptions.AllTeamsDisabledException()
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        query = await session.execute(
            select(MerchantModel.left_eps_change_amount_allowed,
                   MerchantModel.right_eps_change_amount_allowed,
                   MerchantModel.is_whitelist,
                   MerchantModel.min_fiat_amount_in,
                   MerchantModel.max_fiat_amount_in
            ).filter(
                MerchantModel.id == request.merchant_id
            )
        )
        left_eps_change_amount_allowed, right_eps_change_amount_allowed, is_whitelist, min_fiat_amount_in, max_fiat_amount_in = query.first()
    if min_fiat_amount_in * DECIMALS > request.amount or max_fiat_amount_in * DECIMALS < request.amount:
        bank = request.bank
        type = request.type
        if request.bank is None and request.banks and len(request.banks) == 1:
            bank = request.banks[0]
        if request.type is None and request.types and len(request.types) == 1:
            type = request.types[0]
        if request.payment_systems and len(request.payment_systems) == 1:
            payment_system = request.payment_systems[0]
        else:
            payment_system = None
        current_time = int(datetime.utcnow().timestamp())
        unique_id = str(uuid.uuid4())
        error_key = f"/count/errors/450/{request.merchant_id}/{type}/{bank}/{payment_system}/{str(request.is_vip).lower()}"
        await redis.rediss.zadd(
            error_key,
            {f"{current_time}:{unique_id}": current_time}
        )
        await redis.rediss.sadd(f"/count/errors/450/index/{request.merchant_id}", error_key)
        log_data = AllTeamsDisabledLogSchema(
            request_id=request_id,
            merchant_id=request.merchant_id,
            payer_id=request.merchant_payer_id,
            amount=request.amount,
            type=type,
            bank=bank,
            banks=request.banks,
            types=request.types,
            payment_systems=request.payment_systems,
            is_vip=request.is_vip,
            is_whitelist=min(is_whitelist, request.is_vip),
            merchant_transaction_id=request.merchant_transaction_id,
        )

        logger.info(log_data.model_dump_json())
        logger.info(
            f"[AllTeamsDisabledException] - payer_id = {request.merchant_payer_id}, merchant_id = {request.merchant_id}, amount = {request.amount}, type = {type}, bank = {bank}, banks = {request.banks}, types = {request.types}, payment_systems = {request.payment_systems}, is_vip = {request.is_vip}, is_whitelist = {min(is_whitelist, request.is_vip)}, merchant_transaction_id = {request.merchant_transaction_id}"
        )
        raise exceptions.AllTeamsDisabledException()
    set_of_complements = await get_rand_complements(request.amount, left_eps_change_amount_allowed, right_eps_change_amount_allowed)
    num_amount = 0
    size_of_set = len(set_of_complements)
    for new_amount in sorted(set_of_complements):
        async with async_session() as session:
            #await session.begin()
            num_amount += 1
            try:
                log_data = GetBankDetailLogSchema(
                    request_id=request_id,
                    merchant_transaction_id=request.merchant_transaction_id,
                    amount=request.amount,
                    type=request.type,
                    merchant_id=request.merchant_id,
                    payer_id=request.merchant_payer_id,
                    new_amount=new_amount,
                    is_vip=request.is_vip,
                    is_whitelist=is_whitelist,
                    bank=request.bank,
                    banks=request.banks,
                    types=request.types,
                    payment_systems=request.payment_systems,
                    final=(num_amount == size_of_set),
                )
                logger.info(log_data.model_dump_json())
                logger.info(
                    "[GetBankDetail] - "
                    f"merchant_transaction_id = {request.merchant_transaction_id}, "
                    f"amount = {request.amount}, "
                    f"type = {request.type}, "
                    f"merchant_id = {request.merchant_id}, "
                    f"payer_id = {request.merchant_payer_id}, "
                    f"new_amount = {new_amount}, "
                    f"is_vip = {request.is_vip}, "
                    f"is_whitelist = {is_whitelist}, "
                    f"bank = {request.bank}, "
                    f"banks = {request.banks}, "
                    f"types = {request.types}, "
                    f"payment_systems = {request.payment_systems}, "
                    f"final = {'true' if num_amount == size_of_set else 'false'}"
                )

                bank_detail = await get_bank_detail_for_merchant_(
                    type=request.type,
                    merchant_id=request.merchant_id,
                    merchant_transaction_id=request.merchant_transaction_id,
                    payer_id=request.merchant_payer_id,
                    amount=new_amount,
                    session=session,
                    is_vip=request.is_vip,
                    is_whitelist=is_whitelist,
                    bank=request.bank,
                    banks=request.banks,
                    types=request.types,
                    payment_systems=request.payment_systems,
                    initial_amount=request.amount,
                    request_id=request_id,
                    final=True if num_amount == size_of_set else False,
                )

                logger.info(
                    f"[GetBankDetail] - merchant_transaction_id = {request.merchant_transaction_id} result = {bank_detail.bank_detail.__dict__}"
                )
            except exceptions.AllTeamsDisabledException as e:
                if num_amount != size_of_set:
                    logger.info(
                        f"[GetBankDetail] - merchant_transaction_id = {request.merchant_transaction_id} failed; going next iteration;"
                    )
                    continue
                raise e
            except Exception as e:
                logger.info(
                    f"[GetBankDetail] - merchant_transaction_id = {request.merchant_transaction_id}, error = {e}"
                )
                raise e

            economic_model = (await v2_user_get_by_id(bank_detail.team_id, session)).economic_model
            transaction_auto_close_time_s = (
                await v2_user_get_by_id(request.merchant_id, session)).transaction_auto_close_time_s

            request.amount = new_amount
            request = await change_tag_code(request)
            data = request.__dict__
            data["amount"] = new_amount
            del data["type"]
            create = ETs.RequestCreateDB(
                **data,
                type=bank_detail.bank_detail.type,
                direction=Direction.INBOUND,
                status=Status.PENDING,
                bank_detail_id=bank_detail.bank_detail.id,
                currency_id=bank_detail.currency_id,
                bank_detail_number=bank_detail.bank_detail.number,
                bank_detail_name=bank_detail.bank_detail.name,
                bank_detail_bank=bank_detail.bank_detail.bank,
                economic_model=economic_model,
                team_id=bank_detail.team_id,
                additional_info=None,
            )
            try:
                result = await external_transaction_create_(
                    create=create,
                    session=session,
                    request_id=request_id,
                    id=id
                )
            except Exception as e:
                logger.info(
                    f"[CreateTransactionError] - error = {e}, create params = {create.__dict__}, id = {id}"
                )
                raise e
            result.transaction_auto_close_time_s = transaction_auto_close_time_s
            resp = v2_ETs.H2HInboundResponse(
                **result.__dict__, bank_detail=bank_detail.bank_detail,
                payment_link=_get_payment_link(
                    base_url=req.base_url,
                    transaction_type=bank_detail.bank_detail.type,
                    bank=bank_detail.bank_detail.bank,
                    target=bank_detail.bank_detail.number,
                    amount=result.amount
                )
            )
            resp.bank_detail.bank = ASSOCIATE_BANK.get(bank_detail.bank_detail.bank, bank_detail.bank_detail.bank)
            stmt = (
                update(BankDetailModel)
                .where(BankDetailModel.id == result.bank_detail_id)
                .values(pending_count=BankDetailModel.pending_count + 1,
                        today_amount_used=case(
                            (func.date(BankDetailModel.last_transaction_timestamp) < func.date(func.now()),
                             result.amount // DECIMALS),
                            else_=BankDetailModel.today_amount_used + (result.amount // DECIMALS)
                        ),
                        today_transactions_count=case(
                            (
                                func.date(BankDetailModel.last_transaction_timestamp) < func.date(func.now()),
                                0
                            ),
                            else_=BankDetailModel.today_transactions_count
                        ),
                        last_transaction_timestamp=func.now()
                )
            )
            await session.execute(stmt)
            stmt2 = (
                update(TeamModel)
                .where(TeamModel.id == result.team_id)
                .values(count_pending_inbound=TeamModel.count_pending_inbound + 1)
            )
            await session.execute(stmt2)
            await session.commit()
        asyncio.ensure_future(
            close_after_timeout(
                transaction_id=result.id,
                team_id=result.team_id,
                transaction_auto_close_time_s=transaction_auto_close_time_s,
            )
        )
        return resp


async def h2h_create_outbound(request: v2_ETs.H2HCreateOutbound):
    # request = await change_tag_code(request)
    request.bank_detail_bank = ASSOCIATE_MERCHANT_BANK.get(request.bank_detail_bank, request.bank_detail_bank)
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        merchant = await v2_user_get_by_id(request.merchant_id, session)
        economic_model = merchant.economic_model
        transaction_auto_close_time_s = merchant.transaction_auto_close_time_s
        create = ETs.RequestCreateDB(
            **request.__dict__,
            direction=Direction.OUTBOUND,
            status=Status.PENDING,
            team_id=None,
            additional_info=None,
            economic_model=economic_model,
            bank_detail_id=None,
        )
        try:
            result = await external_transaction_create_(
                create=create,
                session=session,
                request_id=request_id,
            )
        except Exception as e:
            logger.info(
                f"[CreateTransactionError] - error = {e}, create params = {create.__dict__}"
            )
            raise e
        if request.type == Type.CARD and request.bank_detail_bank is None:
            asyncio.ensure_future(bcheck.set_bank(transaction_id=result.id, number=request.bank_detail_number[:6]))
        return v2_ETs.H2HOutboundResponse(**result.__dict__)


async def change_tag_code(request: v2_ETs.H2HCreateInbound | v2_ETs.H2HCreateOutbound):
    if type(request) is v2_ETs.H2HCreateInbound:
        return await change_tag_code_inbound(request)
    else:
        return request
    return request


def build_outbound_filters_(request: v2_ETs.GetOutboundRequestDB):
    filter_list = []
    if request.amount_from is not None:
        filter_list.append(ExternalTransactionModel.amount >= request.amount_from)
    if request.amount_to is not None:
        filter_list.append(ExternalTransactionModel.amount <= request.amount_to)
    if request.external_transaction_id is not None:
        filter_list.append(
            ExternalTransactionModel.id == request.external_transaction_id
        )
    if request.tags is not None:
        if None in request.tags:
            filter_list.append(
                or_(
                    ExternalTransactionModel.type.in_(request.tags),
                    ExternalTransactionModel.type is None,
                )
            )
        else:
            filter_list.append(ExternalTransactionModel.type.in_(request.tags))
    if request.banks is not None:
        if None in request.banks:
            filter_list.append(
                or_(
                    ExternalTransactionModel.bank_detail_bank.in_(request.banks),
                    ExternalTransactionModel.bank_detail_bank is None,
                )
            )
        else:
            filter_list.append(
                ExternalTransactionModel.bank_detail_bank.in_(request.banks)
            )
    return filter_list


async def get_outbound_filters(current_user: UserTeamScheme) -> GetOutboundFiltersResponse:
    team_id = current_user.id
    async with ro_async_session() as session:

        banks_q = await session.execute(
            select(ExternalTransactionModel.bank_detail_bank)
            .join(
                TrafficWeightContractModel,
                and_(
                    team_id == TrafficWeightContractModel.team_id,
                    TrafficWeightContractModel.merchant_id
                    == ExternalTransactionModel.merchant_id,
                    TrafficWeightContractModel.type == ExternalTransactionModel.type
                ),
            )
            .join(
                MerchantModel,
                MerchantModel.id == ExternalTransactionModel.merchant_id
            )
            .filter(
                ExternalTransactionModel.amount >= current_user.fiat_min_outbound * DECIMALS,
                ExternalTransactionModel.amount <= current_user.fiat_max_outbound * DECIMALS,
                or_(
                    TrafficWeightContractModel.outbound_amount_less_or_eq.is_(None),
                    ExternalTransactionModel.amount <= TrafficWeightContractModel.outbound_amount_less_or_eq * DECIMALS
                ),
                or_(
                    TrafficWeightContractModel.outbound_amount_great_or_eq.is_(None),
                    ExternalTransactionModel.amount >= TrafficWeightContractModel.outbound_amount_great_or_eq * DECIMALS
                ),
                or_(
                    TrafficWeightContractModel.outbound_bank_in.is_(None),
                    TrafficWeightContractModel.outbound_bank_in.like(
                        func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                    )
                ),
                or_(
                    TrafficWeightContractModel.outbound_bank_not_in.is_(None),
                    ~TrafficWeightContractModel.outbound_bank_not_in.like(
                        func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                    )
                ),
                (current_user.today_outbound_amount_used + ExternalTransactionModel.amount // DECIMALS) <= current_user.max_today_outbound_amount_used,
                ExternalTransactionModel.status == Status.PENDING,
                ExternalTransactionModel.team_id == null(),
                ExternalTransactionModel.create_timestamp +
                func.make_interval(0, 0, 0, 0, 0, 0, MerchantModel.transaction_outbound_auto_close_time_s) >=
                func.now() + text(f"interval '{BEFORE_CLOSE_OUT_EXTERNAL_TRANSACTIONS_S} seconds'"),
                TrafficWeightContractModel.outbound_traffic_weight > 0,
                TrafficWeightContractModel.is_deleted == false(),
            )
            .distinct()
        )
        banks = [i[0] for i in banks_q.all()]

        tags_q = await session.execute(
            select(
                ExternalTransactionModel.type,
                ExternalTransactionModel.type,
                ExternalTransactionModel.type,
            )
            .join(
                TrafficWeightContractModel,
                and_(
                    team_id == TrafficWeightContractModel.team_id,
                    TrafficWeightContractModel.merchant_id
                    == ExternalTransactionModel.merchant_id,
                    TrafficWeightContractModel.type == ExternalTransactionModel.type
                ),
            )
            .join(
                MerchantModel,
                MerchantModel.id == ExternalTransactionModel.merchant_id
            )
            .filter(
                ExternalTransactionModel.amount >= current_user.fiat_min_outbound * DECIMALS,
                ExternalTransactionModel.amount <= current_user.fiat_max_outbound * DECIMALS,
                or_(
                    TrafficWeightContractModel.outbound_amount_less_or_eq.is_(None),
                    ExternalTransactionModel.amount <= TrafficWeightContractModel.outbound_amount_less_or_eq * DECIMALS
                ),
                or_(
                    TrafficWeightContractModel.outbound_amount_great_or_eq.is_(None),
                    ExternalTransactionModel.amount >= TrafficWeightContractModel.outbound_amount_great_or_eq * DECIMALS
                ),
                or_(
                    TrafficWeightContractModel.outbound_bank_in.is_(None),
                    TrafficWeightContractModel.outbound_bank_in.like(
                        func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                    )
                ),
                or_(
                    TrafficWeightContractModel.outbound_bank_not_in.is_(None),
                    ~TrafficWeightContractModel.outbound_bank_not_in.like(
                        func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                    )
                ),
                (current_user.today_outbound_amount_used + ExternalTransactionModel.amount // DECIMALS) <= current_user.max_today_outbound_amount_used,
                ExternalTransactionModel.status == Status.PENDING,
                ExternalTransactionModel.team_id == null(),
                ExternalTransactionModel.create_timestamp +
                func.make_interval(0, 0, 0, 0, 0, 0, MerchantModel.transaction_outbound_auto_close_time_s) >=
                func.now() + text(f"interval '{BEFORE_CLOSE_OUT_EXTERNAL_TRANSACTIONS_S} seconds'"),
                TrafficWeightContractModel.outbound_traffic_weight > 0,
                TrafficWeightContractModel.is_deleted == false(),
            )
            .distinct()
        )
        tags = [
            TagScheme(
                id=tag[0],
                name=USUAL_TYPES_INFO.get(tag[1], {}).get("title", tag[1]),
                code=tag[2],
                create_timestamp=str(datetime.now()),
            )
            for tag in tags_q.all()
        ]
    
    return v2_ETs.GetOutboundFiltersResponse(banks=banks, tags=tags)


async def set_new_exchange_rate_to_outbound(locked_outbound: ExternalTransactionModel,
                                            session: AsyncSession):  # TODO check for concurrency
    currency_id = (await session.execute(
            select(MerchantModel.currency_id)
            .where(MerchantModel.id == locked_outbound.merchant_id)
        )).scalar_one_or_none()
    if not currency_id:
        raise exceptions.CurrencyNotFoundException()
    currency: CurrencyModel = (await session.execute(select(CurrencyModel).where(CurrencyModel.id == currency_id))).scalar_one_or_none()
    if not currency:
        raise exceptions.CurrencyNotFoundException()

    usdt_balance_change = locked_outbound.amount * DECIMALS // currency.outbound_exchange_rate

    ubcm_rec: UserBalanceChangeModel | None = (await session.execute(
        select(UserBalanceChangeModel)
        .filter(UserBalanceChangeModel.transaction_id == locked_outbound.id,
                UserBalanceChangeModel.user_id == locked_outbound.merchant_id
                ).with_for_update())).scalars().first()
    if not ubcm_rec:
        raise exceptions.CurrencyNotFoundException()

    print(ubcm_rec)
    usdt_locked_delta = ubcm_rec.locked_balance - usdt_balance_change
    usdt_trust_delta = ubcm_rec.trust_balance + usdt_balance_change

    ubcm_rec.trust_balance = -usdt_balance_change
    ubcm_rec.locked_balance = usdt_balance_change
    locked_outbound.exchange_rate = currency.outbound_exchange_rate
    await session.execute(
        update(UserBalanceChangeNonceModel)
        .filter(
            UserBalanceChangeNonceModel.balance_id == ubcm_rec.balance_id)
        .values(
            {
                UserBalanceChangeNonceModel.trust_balance: UserBalanceChangeNonceModel.trust_balance - usdt_trust_delta,
                UserBalanceChangeNonceModel.locked_balance: UserBalanceChangeNonceModel.locked_balance - usdt_locked_delta
            }
        ))


async def hold_external_transaction(id: str, current_user: UserTeamScheme):
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        transaction_model = await _find_external_transaction_by_id(
            transaction_id=id,
            session=session,
        )
        if transaction_model.direction != Direction.OUTBOUND:
            raise exceptions.ExternalTransactionExistingDirectionException(
                directions=[Direction.OUTBOUND]
            )
        geo_settings_q = await session.execute(
            select(GeoSettingsModel.max_count_hold).where(GeoSettingsModel.id == current_user.geo.id)
        )
        max_count_hold = geo_settings_q.scalar()
        if transaction_model.count_hold >= max_count_hold:
            raise exceptions.ExternalTransactionHoldLimit()

        merchant_params_q = await session.execute(
            select(
                MerchantModel.transaction_auto_close_time_s,
                MerchantModel.transaction_outbound_auto_close_time_s
            ).where(MerchantModel.id == transaction_model.merchant_id)
        )
        merchant_params = merchant_params_q.first()
        transaction_auto_close_time_s = merchant_params[0]
        transaction_outbound_auto_close_time_s = merchant_params[1]
        transaction_model.transfer_to_team_timestamp = func.now()
        transaction_model.count_hold += 1
        await session.commit()
        await session.refresh(transaction_model)
        result = ETs.Response(**transaction_model.__dict__,
                              transaction_auto_close_time_s=transaction_auto_close_time_s,
                              transaction_outbound_auto_close_time_s=transaction_outbound_auto_close_time_s)
        name_q = await session.execute(
            select(UserModel.name).where(UserModel.id == transaction_model.team_id)
        )
        team_name = name_q.scalar()
        log_data = HoldOutboundTransactionLogSchema(
            request_id=request_id,
            team_name=team_name,
            team_id=transaction_model.team_id,
            transaction_id=transaction_model.id,
            count_hold=transaction_model.count_hold
        )

        logger.info(log_data.model_dump_json())
        logger.info(f"[HoldOutboundTransaction] - team_name = {team_name}, team_id = {transaction_model.team_id}, transaction_id = {transaction_model.id}, count_hold = {transaction_model.count_hold}, UTC_time = {datetime.utcnow()}")
        return result


async def get_outbound(get_outbound_request: v2_ETs.GetOutboundRequestDB, current_user: UserTeamScheme) -> ETs.Response:
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        geo_settings_q = await session.execute(
            select(
                GeoSettingsModel.max_outbound_pending_per_token,
                GeoSettingsModel.auto_close_outbound_transactions_s
            ).where(GeoSettingsModel.id == current_user.geo.id)
        )
        max_pending_limit, auto_close_timeout = geo_settings_q.one()
        await session.execute(text("SELECT pg_advisory_xact_lock(:lock_key)"),
                              {"lock_key": int(UUID(current_user.id).int & 0x7FFFFFFFFFFFFFFF)})
        outbound_check_limit_q = await session.execute(
            select(func.count())
            .select_from(ExternalTransactionModel)
            .filter(
                ExternalTransactionModel.status == Status.PENDING,
                ExternalTransactionModel.team_id == get_outbound_request.team_id,
                ExternalTransactionModel.direction == Direction.OUTBOUND,
            )
        )
        outbound_check_limit = outbound_check_limit_q.scalars().first()
        if (current_user.max_outbound_pending_per_token is None and outbound_check_limit >= max_pending_limit) or (current_user.max_outbound_pending_per_token and outbound_check_limit >= current_user.max_outbound_pending_per_token):
            raise exceptions.MaxOutboundPendingPerTokenException()

        subq = (
            select(1)
            .select_from(TransferAssociationModel)
            .filter(
                TransferAssociationModel.transaction_id == ExternalTransactionModel.id,
                TransferAssociationModel.team_id == current_user.id
            )
        )

        outbound_q = await session.execute(
            select(
                ExternalTransactionModel,
                MerchantModel.transaction_auto_close_time_s,
                MerchantModel.transaction_outbound_auto_close_time_s
            )
            .join(
                TrafficWeightContractModel,
                and_(
                    get_outbound_request.team_id == TrafficWeightContractModel.team_id,
                    TrafficWeightContractModel.merchant_id
                    == ExternalTransactionModel.merchant_id,
                    TrafficWeightContractModel.type == ExternalTransactionModel.type
                ),
            )
            .join(
                MerchantModel,
                MerchantModel.id == ExternalTransactionModel.merchant_id
            )
            .join(
                GeoSettingsModel,
                GeoSettingsModel.id == MerchantModel.geo_id
            )
            .filter(
                ExternalTransactionModel.status == Status.PENDING,
                ExternalTransactionModel.team_id == null(),
                ~exists(subq) if get_outbound_request.external_transaction_id is None else true(),
                ExternalTransactionModel.create_timestamp +
                func.make_interval(0, 0, 0, 0, 0, 0, MerchantModel.transaction_outbound_auto_close_time_s) >=
                func.now() + text(f"interval '{BEFORE_CLOSE_OUT_EXTERNAL_TRANSACTIONS_S} seconds'"),
                TrafficWeightContractModel.outbound_traffic_weight > 0,
                TrafficWeightContractModel.is_deleted == false(),
                ExternalTransactionModel.amount >= current_user.fiat_min_outbound * DECIMALS,
                ExternalTransactionModel.amount <= current_user.fiat_max_outbound * DECIMALS,
                (current_user.today_outbound_amount_used + ExternalTransactionModel.amount // DECIMALS) <= current_user.max_today_outbound_amount_used,
                ExternalTransactionModel.transfer_count < GeoSettingsModel.max_transfer_count,
                or_(
                    TrafficWeightContractModel.outbound_amount_less_or_eq.is_(None),
                    ExternalTransactionModel.amount <= TrafficWeightContractModel.outbound_amount_less_or_eq * DECIMALS
                ),
                or_(
                    TrafficWeightContractModel.outbound_amount_great_or_eq.is_(None),
                    ExternalTransactionModel.amount >= TrafficWeightContractModel.outbound_amount_great_or_eq * DECIMALS
                ),
                or_(
                    TrafficWeightContractModel.outbound_bank_in.is_(None),
                    TrafficWeightContractModel.outbound_bank_in.like(
                        func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                    )
                ),
                or_(
                    TrafficWeightContractModel.outbound_bank_not_in.is_(None),
                    ~TrafficWeightContractModel.outbound_bank_not_in.like(
                        func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                    )
                ),
                *build_outbound_filters_(get_outbound_request),
            )
            .order_by(ExternalTransactionModel.create_timestamp)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        res = outbound_q.first()
        if res is None:
            raise exceptions.NoOutboundExternalTransactionInPoolException()
        outbound = res[0]
        await set_new_exchange_rate_to_outbound(outbound, session=session)
        transaction_auto_close_time_s = res[1]
        transaction_outbound_auto_close_time_s = res[2]
        outbound.team_id = get_outbound_request.team_id
        outbound.transfer_to_team_timestamp = func.now()
        # outbound.currency_id = currency_id
        await session.execute(
            update(TeamModel)
            .where(TeamModel.id == outbound.team_id)
            .values(
                today_outbound_amount_used=case(
                    (func.date(TeamModel.last_transaction_timestamp) < func.date(func.now()),
                    outbound.amount // DECIMALS),
                    else_=TeamModel.today_outbound_amount_used + (outbound.amount // DECIMALS)
                ),
                last_transaction_timestamp=func.now()
            )
        )
        await session.commit()
        await session.refresh(outbound)
        log_data = GetOutboundTransactionLogSchema(
            request_id=request_id,
            team_name=current_user.name,
            team_id=get_outbound_request.team_id,
            transaction_id=outbound.id
        )

        logger.info(log_data.model_dump_json())

        logger.info(f"[GetOutboundTransaction] - team_name = {current_user.name}, team_id = {get_outbound_request.team_id}, transaction_id = {outbound.id}, UTC_time = {datetime.utcnow()}")
        result = ETs.Response(**outbound.__dict__,
                              transaction_auto_close_time_s=transaction_auto_close_time_s,
                              transaction_outbound_auto_close_time_s=transaction_outbound_auto_close_time_s,
                              auto_close_outbound_transactions_s=auto_close_timeout)
        return result


async def h2h_get_transaction_info(request: v2_ETs.H2HGetRequest):
    if request.merchant_transaction_id is None and request.id is None:
        raise exceptions.ExternalTransactionNotFoundException()
    await asyncio.sleep(REPLICATION_LAG_S)
    async with ro_async_session() as session:
        contract_req = await session.execute(
            select(
                ExternalTransactionModel.id,
                ExternalTransactionModel.merchant_transaction_id,
                ExternalTransactionModel.direction,
                ExternalTransactionModel.amount,
                ExternalTransactionModel.status,
                ExternalTransactionModel.create_timestamp,
                func.sum(UserBalanceChangeModel.trust_balance).label(
                    "merchant_trust_change"
                ),
                ExternalTransactionModel.currency_id,
                ExternalTransactionModel.exchange_rate
            )
            .join(
                UserBalanceChangeModel,
                and_(
                    UserBalanceChangeModel.transaction_id
                    == ExternalTransactionModel.id,
                    UserBalanceChangeModel.user_id
                    == ExternalTransactionModel.merchant_id,
                ),
                isouter=True,
            )
            .filter(
                or_(
                    ExternalTransactionModel.id == request.id if request.id is not None else false(),
                    ExternalTransactionModel.merchant_transaction_id == request.merchant_transaction_id if request.merchant_transaction_id is not None else false()
                ),
                ExternalTransactionModel.merchant_id == request.merchant_id if request.merchant_id is not None else true(),
            )
            .group_by(
                ExternalTransactionModel.id,
                ExternalTransactionModel.merchant_transaction_id,
                ExternalTransactionModel.direction,
                ExternalTransactionModel.amount,
                ExternalTransactionModel.status,
                ExternalTransactionModel.create_timestamp,
                ExternalTransactionModel.currency_id,
                ExternalTransactionModel.exchange_rate
            )
        )
        result = contract_req.first()
        print("res", result)
        if result is None:
            raise exceptions.ExternalTransactionNotFoundException()
        return v2_ETs.H2HGetResponse(
            currency_id=result[7],
            exchange_rate=result[8],
            id=result[0],
            merchant_transaction_id=result[1],
            direction=result[2],
            amount=result[3],
            status=result[4],
            create_timestamp=result[5],
            merchant_trust_change=int(result[6]) if result[6] is not None else 0,
        )


def _get_payment_link(base_url, transaction_type, bank, target, amount):
    https_base_url = str(base_url).replace("http", "https")

    link = {
        "sberpay_link": None,
        "tpay_link": None
    }

    if bank == Banks.SBER.name and (transaction_type == Type.PHONE or transaction_type == Type.ACCOUNT):
        data = encrypt_fernet({"phone_number": target, "amount": amount, "type": transaction_type})
        link["sberpay_link"] = f"{https_base_url}payment-link/sber/{data}"

    if (transaction_type == Type.PHONE
        or transaction_type == Type.ACCOUNT
        or transaction_type == Type.CB_PHONE
    ) and bank in BANK_SCHEMAS:
        data = encrypt_fernet({"phone_number": target, "amount": amount, "bank": BANK_SCHEMAS[bank]})
        link["tpay_link"] = f"{https_base_url}payment-link/tpay/{data}"

    return link


async def get_categories(current_user: User):
        if current_user.role == Role.SUPPORT:
            return SUPPORT_OUTBOUND_CATEGORIES
        elif current_user.role == Role.TEAM or current_user.role == Role.MERCHANT:
            return TEAM_OUTBOUND_CATEGORIES

        raise exceptions.NotEnoughPermissionsException()


def get_final_statuses(current_user: User):
    lang = "ru" if current_user.role == Role.TEAM else "en"

    return [
        {
            "name": TRANSACTION_FINAL_STATUS_TITLES[item].get(lang, "en"),
            "code": item.value,
        }
        for item in TransactionFinalStatusEnum
    ]


async def get_team_pending_pay_outs_count(session: AsyncSession, team_id: str):
    subquery = (
        select(ExternalTransactionModel.id)
        .where(
            ExternalTransactionModel.team_id == team_id,
            ExternalTransactionModel.status == Status.PENDING,
            ExternalTransactionModel.direction == Direction.OUTBOUND
        )
        .limit(100)
        .subquery()
    )

    return await session.scalar(select(func.count()).select_from(subquery))


async def get_available_pay_outs_for_team_count(session: AsyncSession, team: UserTeamScheme):
    subq = (
            select(1)
            .select_from(TransferAssociationModel)
            .filter(
                TransferAssociationModel.transaction_id == ExternalTransactionModel.id,
                TransferAssociationModel.team_id == team.id
            )
        )
    
    subquery = (
        select(ExternalTransactionModel.id)
        .join(
            TrafficWeightContractModel,
            and_(
                team.id == TrafficWeightContractModel.team_id,
                TrafficWeightContractModel.merchant_id == ExternalTransactionModel.merchant_id,
                TrafficWeightContractModel.type == ExternalTransactionModel.type
            ),
        )
        .join(
            MerchantModel,
            MerchantModel.id == ExternalTransactionModel.merchant_id
        )
        .join(
            GeoSettingsModel,
            GeoSettingsModel.id == MerchantModel.geo_id
        )
        .where(
            ExternalTransactionModel.status == Status.PENDING,
            ExternalTransactionModel.team_id == null(),
            ~exists(subq),
            ExternalTransactionModel.create_timestamp +
            func.make_interval(0, 0, 0, 0, 0, 0, MerchantModel.transaction_outbound_auto_close_time_s) >=
            func.now() + text(f"interval '{BEFORE_CLOSE_OUT_EXTERNAL_TRANSACTIONS_S} seconds'"),
            TrafficWeightContractModel.outbound_traffic_weight > 0,
            TrafficWeightContractModel.is_deleted == false(),
            ExternalTransactionModel.amount >= team.fiat_min_outbound * DECIMALS,
            ExternalTransactionModel.amount <= team.fiat_max_outbound * DECIMALS,
            (team.today_outbound_amount_used + ExternalTransactionModel.amount // DECIMALS) <= team.max_today_outbound_amount_used,
            ExternalTransactionModel.transfer_count < GeoSettingsModel.max_transfer_count,
            or_(
                TrafficWeightContractModel.outbound_amount_less_or_eq.is_(None),
                ExternalTransactionModel.amount <= TrafficWeightContractModel.outbound_amount_less_or_eq * DECIMALS
            ),
            or_(
                TrafficWeightContractModel.outbound_amount_great_or_eq.is_(None),
                ExternalTransactionModel.amount >= TrafficWeightContractModel.outbound_amount_great_or_eq * DECIMALS
            ),
            or_(
                TrafficWeightContractModel.outbound_bank_in.is_(None),
                TrafficWeightContractModel.outbound_bank_in.like(
                    func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                )
            ),
            or_(
                TrafficWeightContractModel.outbound_bank_not_in.is_(None),
                ~TrafficWeightContractModel.outbound_bank_not_in.like(
                    func.concat('%#', ExternalTransactionModel.bank_detail_bank, '#%')
                )
            )
        )
        .limit(100)
        .subquery()
    )

    return await session.scalar(select(func.count()).select_from(subquery))


async def test_get_bd(i):
    try:
        r = await h2h_create_inbound(
            v2_ETs.H2HCreateInbound(
                merchant_id="0d5edc63-f04d-4dbb-b1b3-55908d736fc4",
                merchant_payer_id=str(time.time()),
                merchant_transaction_id=str(time.time()),
                amount=1000000000,
                hook_uri="",
                type="card",
            )
        )
        print(i, r.bank_detail.number)
    except:
        print(i, "exc")


async def test():
    await asyncio.gather(*[test_get_bd(i) for i in range(2)])
    await asyncio.sleep(1)
    await asyncio.gather(*[test_get_bd(i) for i in range(2)])


if __name__ == "__main__":
    asyncio.run(external_transaction_update_from_device(
        ETs.RequestUpdateFromDeviceDB(
            message='Поступление 50000.00 RUR по СБП от Арсен М.',
            api_secret='d59a367cbca9071a54a2089d6a9582cf3ba0e724159de98d66af63a50a09f668',
            device_hash='DJ3SVA',
            bank='alfabank',
            timestamp=1720003629000 / 1000)))
    # print(asyncio.run(get_bank_detail_for_merchant_(type = "card", merchant_id = "0d5edc63-f04d-4dbb-b1b3-55908d736fc4", amount = 100000000, session=async_session())))
