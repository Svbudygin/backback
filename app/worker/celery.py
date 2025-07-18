import asyncio
from datetime import timedelta, datetime, time
from sqlalchemy.sql.expression import text
from celery import Celery
from datetime import datetime, time, timedelta
import random
import uuid
from celery.utils.log import get_task_logger
from app.core import config, redis
from app.core.session import async_session, ro_async_session
from app.core import constants
from app.core.redis import redis_client_ping
from app.enums import TransactionFinalStatusEnum
from app.services.notification_service import send_notification
from app.schemas.NotificationsSchema import (
    ReqDisabledNotificationSchema,
    ReqDisabledNotificationDataSchema,
    ReqCloseDisabledNotificationSchema,
    ReqIncorrectWorkingNotificationSchema
)
from app.schemas.LogsSchema import *
from app.functions.external_transaction import external_transaction_update_
from app.functions.appeal import accept_appeal_by_system
from app.utils.time import time_without_pause
import base64

redis_url = f"{config.settings.redis_url}/{config.settings.REDIS_CELERY_DB}"

logger = get_task_logger(__name__)

celery_app = Celery(
    __name__,
    broker=redis_url
)

celery_app.conf.event_serializer = 'pickle'
celery_app.conf.task_serializer = 'pickle'
celery_app.conf.result_serializer = 'pickle'
celery_app.conf.accept_content = ['application/json', 'application/x-python-serialize']


# def regenerate_details_daily_task(detail_id: str, transactions_count_limit: list,  is_active: bool = True):
#     if is_active == False:
#         return
#     current_time = datetime.utcnow()
#     all_task_times = []
#
#     for period_data in transactions_count_limit:
#         time_from = period_data[0]
#         time_to = period_data[1]
#         count = period_data[2]
#         seconds = period_data[3]
#
#         time_from = datetime.strptime(time_from, "%H:%M").replace(year=current_time.year, month=current_time.month,
#                                                                   day=current_time.day)
#         time_to = datetime.strptime(time_to, "%H:%M").replace(year=current_time.year, month=current_time.month,
#                                                               day=current_time.day)
#         if time_to < time_from:
#             time_to += timedelta(days=1)
#
#         current_task_times = generate_random_times(count, time_from, time_to, current_time, seconds)
#         all_task_times.extend(current_task_times)
#
#     all_task_times = sorted(all_task_times)
#     first_task_time = all_task_times.pop(0)
#     execute_task_for_bank_detail.apply_async(args=(detail_id, transactions_count_limit, all_task_times), eta=first_task_time)
#
#
# def generate_random_times(count, start, end, current_time, seconds):
#     total_seconds = int((end - start).total_seconds())
#     expanded_count = count * 10
#     random_seconds = sorted(random.sample(range(total_seconds), expanded_count))
#     filtered_times = []
#     for sec in random_seconds:
#         candidate_time = start + timedelta(seconds=sec)
#         if candidate_time >= current_time and (
#                 not filtered_times or (candidate_time - filtered_times[-1]).total_seconds() >= seconds
#         ):
#             filtered_times.append(candidate_time)
#
#     while len(filtered_times) > count:
#         filtered_times.pop(random.randint(0, len(filtered_times) - 1))
#
#     return sorted(filtered_times)
#
#
# @celery_app.task
# def execute_task_for_bank_detail(detail_id: str, transactions_count_limit: list, task_times: list):
#     loop = asyncio.get_event_loop()
#     flag, is_active = loop.run_until_complete(task_for_bank_detail(detail_id, transactions_count_limit))
#     if flag and is_active:
#         if task_times:
#             next_task_time = task_times.pop(0)
#             while next_task_time < datetime.utcnow():
#                 next_task_time = task_times.pop(0)
#             execute_task_for_bank_detail.apply_async(args=(detail_id, transactions_count_limit, task_times),
#                                                          eta=next_task_time)
#         else:
#             regenerate_details_daily_task(detail_id, transactions_count_limit)
# async def task_for_bank_detail(detail_id: str, transactions_count_limit: list):
#     async with async_session() as session:
#         query_check = text("""
#             SELECT pending_count, transactions_count_limit, is_active
#             FROM bank_detail_model
#             WHERE id = :detail_id
#         """)
#         result = await session.execute(query_check, {'detail_id': detail_id})
#         row = result.fetchone()
#
#         pending_count = row.pending_count
#         db_transactions = list(map(tuple, row.transactions_count_limit))
#         task_transactions = list(map(tuple, transactions_count_limit))
#         if db_transactions != task_transactions or row.is_active == False:
#             return (False, row.is_active)
#
#         if pending_count == 0:
#             query_update = text("""
#                 UPDATE bank_detail_model
#                 SET is_auto_active = TRUE
#                 WHERE id = :detail_id
#             """)
#             await session.execute(query_update, {'detail_id': detail_id})
#             await session.commit()
#         return (True, row.is_active)



@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        timedelta(seconds=constants.Params.AUTO_CLOSE_TRANSACTIONS_INTERVAL_S),
        remove_team_from_old_pending_transactions.s(),
        name='remove old pending transactions'
    )

    sender.add_periodic_task(
        timedelta(seconds=constants.Params.CHECK_DISABLED_DEVICES_INTERVAL_S),
        disable_disconnected_devices.s(),
        name='disable disconnected devices'
    )

    sender.add_periodic_task(
        timedelta(seconds=constants.Params.AUTO_UNBIND_VIP_NO_TRX_S),
        unbind_vip_no_trx.s(),
        name='unbind vip no accept transactions'
    )

    sender.add_periodic_task(
        timedelta(seconds=constants.Params.AUTO_GET_BACK_TRANSACTIONS_INTERVAL_S),
        remove_transfer_association_from_team.s(),
        name='remove transfer association from team'
    )

    sender.add_periodic_task(
        timedelta(seconds=30*60),
        remove_old_450.s(),
        name='remove old 450 exceptions'
    )

    sender.add_periodic_task(
        timedelta(seconds=constants.Params.REMOVE_TRANSFER_ASSOCIATION_INTERVAL_S),
        remove_transfer_association.s(),
        name='remove transfer association'
    )

    sender.add_periodic_task(
        timedelta(seconds=constants.Params.AUTO_ACCEPT_APPEALS_INTERVAL_S),
        auto_accept_appeals.s(),
        name='auto accept appeals'
    )

    sender.add_periodic_task(
        timedelta(seconds=constants.Params.AUTO_CLOSE_PAYOUTS_INTERVAL_S),
        auto_close_payouts_worker.s(),
        name='auto close payouts'
    )

    sender.add_periodic_task(
        timedelta(seconds=constants.Params.DISABLED_REQS_AUTO_CONFIRM_NOT_WORKING_INTERVAL_S),
        disable_reqs_if_auto_confirmation_not_working.s(),
        name='disable reqs if auto confirmation not working'
    )

    sender.add_periodic_task(
        timedelta(seconds=60),
        disable_many_close_in_trans_details.s(),
        name='disable details with many close transactions'
    )


@celery_app.task
def disable_disconnected_devices():
    logger.info('will disable disconnected devices')


@celery_app.task
def remove_team_from_old_pending_transactions():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_remove_team_from_old_pending_transactions())
    return result


@celery_app.task
def disable_disconnected_devices():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_disable_disconnected_devices())
    return result


@celery_app.task
def unbind_vip_no_trx():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_unbind_vip_no_trx())
    return result


@celery_app.task
def remove_transfer_association_from_team():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_remove_transfer_association_from_team())
    return result

@celery_app.task
def remove_old_450():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_remove_old_450())
    return result


@celery_app.task
def remove_transfer_association():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_remove_transfer_association())
    return result


@celery_app.task
def auto_accept_appeals():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_auto_accept_appeals())
    return result


@celery_app.task
def auto_close_payouts_worker():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_auto_close_payouts_worker())
    return result


@celery_app.task
def disable_reqs_if_auto_confirmation_not_working():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_disable_reqs_if_auto_confirmation_not_working())
    return result


@celery_app.task
def disable_many_close_in_trans_details():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(_disable_many_close_in_trans_details())
    return result


async def _remove_old_450():
    current_time = int(datetime.utcnow().timestamp())
    threshold_time = current_time - 86400
    pattern = "/count/errors/450/*/*/*/*/*"
    cursor = 0
    total_deleted = 0
    total_keys_scanned = 0
    while True:
        cursor, keys = await redis.rediss.scan(cursor=cursor, match=pattern, count=500)
        if keys:
            pipeline = redis.rediss.pipeline()
            for key in keys:
                pipeline.zremrangebyscore(key, 0, threshold_time)
            results = await pipeline.execute()
            total_deleted += sum(result or 0 for result in results)
            total_keys_scanned += len(keys)
        if cursor == 0:
            break

    logger.info(f"Redis cleanup finished: {total_deleted} elements removed from {total_keys_scanned} keys.")


def decode_bank_detail_hash(encoded: str) -> str:
    try:
        return base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return "<invalid base64>"


async def _unbind_vip_no_trx():
    async with async_session() as session:
        query = text("""
            WITH inactive_profiles AS (
                SELECT profile_id
                FROM bank_detail_model
                GROUP BY profile_id
                HAVING BOOL_AND(is_vip = FALSE)
                   AND BOOL_AND(update_timestamp <= NOW() - INTERVAL '24 hours')
            ),
            deleted_vip_payers AS (
                DELETE FROM vip_payer_model vpm
                WHERE (
                        (
                            vpm.last_accept_timestamp IS NULL AND EXISTS (
                                SELECT 1
                                FROM external_transaction_model ext
                                JOIN bank_detail_model bdm ON bdm.id = ext.bank_detail_id
                                WHERE ext.merchant_payer_id = vpm.payer_id
                                  AND bdm.profile_id = vpm.bank_detail_id
                                  AND ext.status != 'pending'
                            )
                        )
                        OR vpm.bank_detail_id IN (SELECT profile_id FROM inactive_profiles)
                        OR NOT EXISTS (
                            SELECT 1
                            FROM bank_detail_model bdm_check
                            WHERE bdm_check.profile_id = vpm.bank_detail_id
                              AND bdm_check.is_deleted = FALSE
                        )
                    )
                  AND NOT EXISTS (
                        SELECT 1
                        FROM external_transaction_model ext
                        JOIN bank_detail_model bdm ON bdm.id = ext.bank_detail_id
                        WHERE ext.merchant_payer_id = vpm.payer_id
                          AND bdm.profile_id = vpm.bank_detail_id
                          AND ext.status = 'pending'
                    )
                RETURNING 
                    vpm.payer_id,
                    vpm.bank_detail_id AS profile_id,
                    CASE
                        WHEN vpm.last_accept_timestamp IS NULL AND EXISTS (
                            SELECT 1
                            FROM external_transaction_model ext
                            JOIN bank_detail_model bdm ON bdm.id = ext.bank_detail_id
                            WHERE ext.merchant_payer_id = vpm.payer_id
                              AND bdm.profile_id = vpm.bank_detail_id
                              AND ext.status != 'pending'
                        ) THEN 'never accepted but had non-pending transaction'
            
                        WHEN vpm.bank_detail_id IN (SELECT profile_id FROM inactive_profiles)
                            THEN 'not VIP and not changed for 24h'
            
                        WHEN NOT EXISTS (
                            SELECT 1
                            FROM bank_detail_model bdm_check
                            WHERE bdm_check.profile_id = vpm.bank_detail_id
                              AND bdm_check.is_deleted = FALSE
                        ) THEN 'profile_id is unknown'
            
                        ELSE 'unknown'
                    END AS delete_reason
            ),
            affected_profiles AS (
                SELECT profile_id, COUNT(*) AS deleted_count
                FROM deleted_vip_payers
                GROUP BY profile_id
            ),
            updated_bank_detail_counters AS (
                UPDATE bank_detail_model bdm
                SET count_vip_payers = GREATEST(0, bdm.count_vip_payers - ap.deleted_count)
                FROM affected_profiles ap
                WHERE bdm.profile_id = ap.profile_id
                RETURNING bdm.id AS updated_id, bdm.profile_id
            )
            SELECT 
                dvp.payer_id,
                dvp.profile_id,
                dvp.delete_reason,
                ubc.updated_id
            FROM deleted_vip_payers dvp
            LEFT JOIN updated_bank_detail_counters ubc 
              ON dvp.profile_id = ubc.profile_id;
        """)

        result = await session.execute(query)
        deleted = result.fetchall()
        await session.commit()

        if deleted:
            for payer_id, profile_id, reason, updated_id in deleted:
                logger.info(
                    f"[UnbindVipPayer] - payer_id={payer_id}, profile_id={profile_id}, updated_bank_detail_id={updated_id}, reason={reason}"
                )
        else:
            logger.info("No VIP payers to unbind.")


async def _remove_team_from_old_pending_transactions():
    async with async_session() as session:
        select_query = text(f"""
            SELECT etm.id, etm.team_id, um.name, etm.amount
            FROM external_transaction_model etm
            JOIN user_model um ON etm.team_id = um.id
            JOIN merchants m ON etm.merchant_id = m.id
            JOIN geo_settings gs ON m.geo_id = gs.id
            WHERE etm.team_id IS NOT NULL
              AND etm.transfer_to_team_timestamp IS NOT NULL
              AND etm.direction = 'outbound'
              AND etm.status = 'pending'
              AND etm.transfer_to_team_timestamp < NOW() - (gs.auto_close_outbound_transactions_s || ' SECOND')::INTERVAL
            FOR UPDATE OF etm
        """)
        result = await session.execute(select_query)
        rows = result.fetchall()

        if not rows:
            logger.info("No external transactions to update for team unbinding.")
            return

        ids_to_update_transactions = []
        team_amounts_to_subtract = {}
        UTC_time = datetime.utcnow()
        request_id = str(uuid.uuid4())
        for row in rows:
            ids_to_update_transactions.append(row.id)
            log_data = UnbindOutboundTransactionLogSchema(
                request_id=request_id,
                team_name=row.name,
                team_id=row.team_id,
                transaction_id=row.id
            )
            logger.info(log_data.model_dump_json())
            logger.info(f"[UnbindOutboundTransaction] - team_name = {row.name}, team_id = {row.team_id}, transaction_id = {row.id}, UTC_time = {UTC_time}")
            team_amounts_to_subtract[row.team_id] = team_amounts_to_subtract.get(row.team_id, 0) + (row.amount // 1000000)

        if ids_to_update_transactions:
            update_transactions_query = text("""
                UPDATE external_transaction_model
                SET team_id = NULL, transfer_to_team_timestamp = NULL, count_hold = 0
                WHERE id = ANY(:ids)
            """)
            await session.execute(update_transactions_query, {"ids": ids_to_update_transactions})
            logger.info(f"Unbind {len(ids_to_update_transactions)} external transactions from teams.")

        if team_amounts_to_subtract:
            values_clauses = [f"('{team_id}', {total_amount})" for team_id, total_amount in team_amounts_to_subtract.items() if total_amount > 0]
            if values_clauses:
                values_string = ", ".join(values_clauses)
                update_teams_query_sql = f"""
                    UPDATE teams t
                    SET today_outbound_amount_used = 
                        CASE
                            WHEN DATE(t.last_transaction_timestamp) < CURRENT_DATE THEN 0
                            ELSE GREATEST(0, t.today_outbound_amount_used - v.amount_to_subtract)
                        END
                    FROM (VALUES {values_string}) AS v(id, amount_to_subtract)
                    WHERE t.id = v.id;
                """
                await session.execute(text(update_teams_query_sql))

        await session.commit()

async def _remove_transfer_association_from_team():
    async with async_session() as session:
        delete_query = text(f"""
            DELETE FROM transfer_association_model
            USING
                external_transaction_model,
                user_model,
                merchants,
                geo_settings
            WHERE
                external_transaction_model.id = transfer_association_model.transaction_id
                AND user_model.id = transfer_association_model.team_id
                AND merchants.id = external_transaction_model.merchant_id
                AND geo_settings.id = merchants.geo_id
                AND transfer_from_team_timestamp < NOW() - (geo_settings.get_back_transactions_time_s || ' SECOND')::INTERVAL
            RETURNING transfer_association_model.team_id, transfer_association_model.transaction_id, external_transaction_model.status, user_model.name
        """)
        result = await session.execute(delete_query)
        rows = result.fetchall()
        request_id = str(uuid.uuid4())
        if rows:
            UTC_time = datetime.utcnow()
            for row in rows:
                if row.status == 'pending':
                    log_data = DeleteTransferAssociationTransactionLogSchema(
                        request_id=request_id,
                        team_name=row.name,
                        team_id=row.team_id,
                        transaction_id=row.transaction_id
                    )

                    logger.info(log_data.model_dump_json())
                    logger.info(f"[DeleteTransferAssociationTransaction] - team_name = {row.name}, team_id = {row.team_id}, transaction_id = {row.transaction_id}, UTC_time = {UTC_time}")
        else:
            logger.info("No outbound transactions to delete association")
        await session.commit()


async def _disable_disconnected_devices():
    now = datetime.now()
    last_allowed_time = now - timedelta(seconds=constants.Params.DISABLED_DEVICE_PING_DELAY_S)

    devices_hashes_to_disable = []

    async for key in redis_client_ping.scan_iter(match='*'):
        timestamp = await redis_client_ping.get(key)
        datetime_obj = datetime.fromtimestamp(int(timestamp))

        if datetime_obj < last_allowed_time:
            devices_hashes_to_disable.append(key.decode('utf-8'))

    async with async_session() as session:
        query = text("""
            UPDATE bank_detail_model
            SET is_active = FALSE, update_timestamp = NOW()
            WHERE device_hash = ANY(:device_hashes) AND is_active = TRUE
            RETURNING id, team_id, number;
        """)

        ids_to_disable = []
        result = await session.execute(query, {'device_hashes': devices_hashes_to_disable})
        for row in result:
            ids_to_disable.append(row.id)
            await send_notification(ReqDisabledNotificationSchema(
                team_id=row.team_id,
                data=ReqDisabledNotificationDataSchema(
                    number=row.number
                )
            ))

        await session.commit()

    if len(devices_hashes_to_disable) > 0:
        await redis_client_ping.delete(*devices_hashes_to_disable)

    logger.info(f"Disabled {devices_hashes_to_disable} devices")
    logger.info(f"[UpdateDetail] - Disabled ids by reason of bad ping = {ids_to_disable}")


async def _remove_transfer_association():
    logger.info("[_remove_transfer_association] received")
    async with async_session() as session:
        query = text(f"""
            SELECT tam.transaction_id
            FROM transfer_association_model tam
            JOIN external_transaction_model etm ON tam.transaction_id = etm.id
            JOIN merchants m ON etm.merchant_id = m.id
            JOIN geo_settings gs ON m.geo_id = gs.id
            WHERE etm.status = 'pending' AND etm.team_id IS NULL
            GROUP BY tam.transaction_id, gs.max_transfer_count
            HAVING COUNT(*) >= gs.max_transfer_count
            LIMIT 10
        """)

        result = await session.execute(query)

        transaction_ids = [row[0] for row in result]

        if not transaction_ids:
            logger.info("[_remove_transfer_association]: no transactions matching criteria")
            return

        for tid in transaction_ids:
            try:
                await external_transaction_update_(
                    transaction_id=tid,
                    session=session,
                    status=constants.Status.CLOSE,
                    close_if_accept=False,
                    final_status=TransactionFinalStatusEnum.AUTO
                )

                delete_query = text("DELETE FROM transfer_association_model WHERE transaction_id = :tid")
                await session.execute(delete_query, {"tid": tid})
                session.commit()
                logger.info(f"[_remove_transfer_association]: deleted records with transaction_id = {tid}")
            except Exception as e:
                logger.info(f"[_remove_transfer_association]: error processing transaction_id = {tid}: {e}")
                session.rollback()


def _is_in_time_interval(x: time, interval_start: time, interval_end: time):
    if interval_start < interval_end:
        return interval_start <= x <= interval_end
    else:
        return x >= interval_start or x <= interval_end


async def _auto_accept_appeals():
    async with async_session() as session:
        settings_query = text(f"""
            SELECT *
            FROM geo_settings
            WHERE is_auto_accept_appeals_enabled = TRUE AND auto_accept_appeals_downtime_s IS NOT NULL;
        """)

        settings = (await session.execute(settings_query)).all()

        for setting in settings:
            utc_time_now = datetime.utcnow()
            if (not setting.auto_accept_appeals_pause_time_from
                or not setting.auto_accept_appeals_pause_time_to
                or not _is_in_time_interval(utc_time_now.time(), setting.auto_accept_appeals_pause_time_from, setting.auto_accept_appeals_pause_time_to)
            ):
                appeals_query = text(f"""
                    SELECT appeals.id, appeals.team_processing_start_time
                    FROM appeals
                    JOIN external_transaction_model etm ON etm.id = appeals.transaction_id
                    JOIN merchants ON etm.merchant_id = merchants.id
                    WHERE appeals.team_processing_start_time IS NOT NULL AND merchants.geo_id = {setting.id}
                """)

                appeals_to_accept = (await session.execute(appeals_query)).all()
                logger.info(f"[_auto_accept_appeals]: starting for geo_id = {setting.id}, will check {len(appeals_to_accept)} appeals")

                for appeal in appeals_to_accept:
                    try:
                        total_duration_s = 0
                        
                        if setting.auto_accept_appeals_pause_time_from and setting.auto_accept_appeals_pause_time_to:
                            total_duration_s = time_without_pause(
                                appeal.team_processing_start_time,
                                utc_time_now,
                                setting.auto_accept_appeals_pause_time_from,
                                setting.auto_accept_appeals_pause_time_to
                            )
                        else:
                            total_duration_s = int(abs((utc_time_now - appeal.team_processing_start_time).total_seconds()))
                        
                        if total_duration_s >= setting.auto_accept_appeals_downtime_s:
                            await accept_appeal_by_system(session, appeal.id)
                            logger.info(f"[_auto_accept_appeals]: accepted appeal_id = {appeal.id}")
                    except Exception as e:
                        logger.info(f"[_auto_accept_appeals]: error accepting appeal_id = {appeal.id}: {e}")
                        session.rollback()


async def _auto_close_payouts_worker():
    async with async_session() as session:
        settings_query = text(f"""
            SELECT *
            FROM close_payouts_worker_settings
            WHERE is_enabled = TRUE
        """)

        settings = (await session.execute(settings_query)).all()

        for setting in settings:
            conditions = []
            params = {}

            if setting.amount_ge:
                conditions.append("t.amount >= :amount_ge")
                params['amount_ge'] = setting.amount_ge
            
            if setting.amount_le:
                conditions.append("t.amount <= :amount_le")
                params['amount_le'] = setting.amount_le
            
            if setting.type_in:
                conditions.append("t.type = ANY(:type_in)")
                params['type_in'] = setting.type_in
            
            if setting.type_not_in:
                conditions.append("NOT t.type = ANY(:type_not_in)")
                params['type_not_in'] = setting.type_not_in
            
            if setting.bank_in:
                conditions.append("t.bank_detail_bank = ANY(:bank_in)")
                params['bank_in'] = setting.bank_in
            
            if setting.bank_not_in:
                conditions.append("NOT t.bank_detail_bank = ANY(:bank_not_in)")
                params['bank_not_in'] = setting.bank_not_in
            
            if setting.last_seconds:
                conditions.append("(NOW() - t.create_timestamp) >= (:last_seconds || ' seconds')::interval")
                params['last_seconds'] = str(setting.last_seconds)
            
            conditions.append(f"merchants.geo_id = {setting.geo_id}")
            conditions.append("t.team_id IS NULL")
            conditions.append(f"t.direction = '{constants.Direction.OUTBOUND}'")
            conditions.append(f"t.status = '{constants.Status.PENDING}'")

            conditions_string = "\nAND ".join(conditions)

            query = f"""
                SELECT t.id
                FROM external_transaction_model t
                JOIN merchants
                ON t.merchant_id = merchants.id
                WHERE {conditions_string}
                FOR UPDATE OF t SKIP LOCKED
            """

            result = await session.execute(text(query), params)

            ids_to_close = result.scalars().all()

            for id in ids_to_close:
                await external_transaction_update_(
                    transaction_id=id,
                    session=session,
                    status=constants.Status.CLOSE,
                    close_if_accept=False,
                    final_status=TransactionFinalStatusEnum.AUTO
                )

                logger.info(f"[AUTO_CLOSE_PAYOUTS]: closed outbound transaction with id = {id}")


async def _disable_reqs_if_auto_confirmation_not_working():
    async with async_session() as session:
        query = text("""
            WITH bank_details_to_disable AS (
                SELECT
                    bd.team_id AS team_id,
                    bd.id AS bank_detail_id
                FROM bank_detail_model bd
                JOIN external_transaction_model t ON bd.id = t.bank_detail_id
                JOIN teams ON teams.id = bd.team_id
                JOIN geo_settings gs ON teams.geo_id = gs.id
                WHERE t.status = '{constants.Status.PENDING}' AND bd.need_check_automation
                GROUP BY bd.team_id, bd.id, gs.req_after_enable_max_pay_in_count, gs.req_after_enable_max_pay_in_automation_time
                HAVING COUNT(t.id) >= gs.req_after_enable_max_pay_in_count
                    AND MAX(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - t.create_timestamp))) >= gs.req_after_enable_max_pay_in_automation_time
            ),
            updated_bank_details AS (
                UPDATE bank_detail_model
                SET is_active = FALSE, need_check_automation = FALSE
                WHERE id IN (SELECT bank_detail_id FROM bank_details_to_disable)
                RETURNING id
            ),
            updated_teams AS (
                UPDATE teams
                SET priority_inbound = 0
                WHERE id IN (SELECT team_id FROM bank_details_to_disable)
            )
            SELECT
                team_id,
                bank_detail_id
            FROM bank_details_to_disable;
        """)

        result = await session.execute(query)

        await session.commit()

        rows = result.fetchall()

        messages = []
        for row in rows:
            team_id, req = row
            messages.append(f"{team_id} - {req}")
        
            await send_notification(ReqIncorrectWorkingNotificationSchema(
                team_id=team_id,
                data=ReqDisabledNotificationDataSchema(
                    number=req
                )
            ))
        
        message_string = ""
        if messages:
            message_string = "\n".join(messages)
        
        logger.info(f"[DisableReqsIfAutoConfirmationNotWorking] Disabled reqs (team_id - req)\n\n{message_string}")


async def _disable_many_close_in_trans_details():
    async with ro_async_session() as session:
        query = text("""
                    WITH recent_transactions AS (
                        SELECT
                            etm.id,
                            etm.bank_detail_id,
                            etm.status,
                            etm.final_status_timestamp,
                            ROW_NUMBER() OVER (
                                PARTITION BY etm.bank_detail_id
                                ORDER BY etm.final_status_timestamp DESC
                            ) AS row_num
                        FROM external_transaction_model etm
                        JOIN bank_detail_model bdm ON bdm.id = etm.bank_detail_id
                        WHERE etm.final_status_timestamp >= NOW() - INTERVAL '12 hours'
                          AND etm.create_timestamp >= bdm.last_disable
                          AND bdm.is_active = TRUE
                    ),
                    status_flags AS (
                        SELECT
                            *,
                            CASE
                                WHEN status = 'close' THEN 0
                                ELSE 1
                            END AS is_not_close
                        FROM recent_transactions
                    ),
                    rolling_flags AS (
                        SELECT
                            *,
                            SUM(is_not_close) OVER (
                                PARTITION BY bank_detail_id
                                ORDER BY row_num
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                            ) AS first_non_close_group
                        FROM status_flags
                    ),
                    consecutive_close_counts AS (
                        SELECT
                            bank_detail_id,
                            COUNT(*) AS consecutive_close_count
                        FROM rolling_flags
                        WHERE status = 'close' AND first_non_close_group = 0
                        GROUP BY bank_detail_id
                    ),
                    threshold_exceeded_details AS (
                        SELECT
                            bdm.id AS bank_detail_id
                        FROM consecutive_close_counts ccc
                        JOIN bank_detail_model bdm ON bdm.id = ccc.bank_detail_id
                        JOIN teams t ON t.id = bdm.team_id
                        JOIN geo_settings gs ON gs.id = t.geo_id
                        WHERE ccc.consecutive_close_count >= gs.max_inbound_close_count
                    )
                    SELECT bank_detail_id FROM threshold_exceeded_details;
                """)
        result = await session.execute(query)
        bank_detail_ids = result.scalars().all()

    if bank_detail_ids:
        async with async_session() as session:
            upd_query = text("""
                        UPDATE bank_detail_model
                        SET is_active = FALSE, update_timestamp = NOW(), last_disable = NOW()
                        WHERE id = ANY(:bank_detail_ids) AND is_active = TRUE
                        RETURNING id, team_id, number
                    """)
            result = await session.execute(upd_query, {'bank_detail_ids': bank_detail_ids})
            for row in result:
                await send_notification(ReqCloseDisabledNotificationSchema(
                    team_id=row.team_id,
                    data=ReqDisabledNotificationDataSchema(
                        number=row.number
                    )
                ))
            await session.commit()
        logger.info(f"[UpdateDetail] - Disabled ids by reason of many close inbound transactions = {bank_detail_ids}")

