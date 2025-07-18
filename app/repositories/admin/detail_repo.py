import datetime
from sqlalchemy import func, and_, select, update, or_, true, exists, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExternalTransactionModel, UserModel, BankDetailModel, TeamModel, VipPayerModel
from app.schemas.admin.DetailsScheme import *
from app.utils.session import get_session
from app.core.constants import DECIMALS
import logging
import hashlib

logger = logging.getLogger(__name__)

async def time_to_minutes(t: datetime.time) -> int:
    return t.hour * 60 + t.minute
class DetailRepo:
    @staticmethod
    async def get_transaction_counts(
        session: AsyncSession, detail_id: str, period_minutes: int = 60
    ) -> tuple[int, int]:
        time_threshold = datetime.datetime.utcnow() - datetime.timedelta(minutes=period_minutes)

        accepted_count = await session.scalar(
            select(func.count())
            .where(
                and_(
                    ExternalTransactionModel.bank_detail_id == detail_id,
                    ExternalTransactionModel.status == "accept",
                    ExternalTransactionModel.final_status_timestamp >= time_threshold,
                )
            )
        )

        closed_count = await session.scalar(
            select(func.count())
            .where(
                and_(
                    ExternalTransactionModel.bank_detail_id == detail_id,
                    ExternalTransactionModel.status == "close",
                    ExternalTransactionModel.final_status_timestamp >= time_threshold,
                )
            )
        )

        return accepted_count or 0, closed_count or 0

    @classmethod
    async def get(
        cls, session: AsyncSession, detail_id: str, period: int | None
    ) -> AdminBankDetailSchemeResponse | None:
        async with get_session(session) as session:
            query = select(BankDetailModel).where(BankDetailModel.id == detail_id)
            result = await session.execute(query)
            detail_row = result.scalar_one_or_none()

            if not detail_row:
                return None

            accepted, closed = await cls.get_transaction_counts(
                session, detail_id, period_minutes=period
            )

            team = await session.scalar(
                select(UserModel.name).where(UserModel.id == detail_row.team_id)
            )

            conv = accepted / (closed + accepted) if (closed + accepted) > 0 else 0.0

            data = detail_row.__dict__.copy()
            data.pop("today_amount_used", None)
            data.pop("today_transactions_count", None)
            data.pop("period_time", None)

            response = AdminBankDetailSchemeResponse(
                **data,
                today_amount_used=0 if detail_row.last_transaction_timestamp.date() < datetime.datetime.utcnow().date() else detail_row.today_amount_used,
                today_transactions_count=0 if detail_row.last_transaction_timestamp.date() < datetime.datetime.utcnow().date() else detail_row.today_transactions_count,
                team_name=team,
                accepted=accepted,
                closed=closed,
                conv=int(conv * 100),
                period_time = [
                    await time_to_minutes(detail_row.period_start_time),
                    await time_to_minutes(detail_row.period_finish_time)
                ] if detail_row.period_start_time and detail_row.period_finish_time else None,
            )

            return response

    @classmethod
    async def get_search_filters(cls, request: AdminBankDetailSchemeRequestList):
        search_without_plus = (request.search or "").replace("+", "")

        model = BankDetailModel
        queries_none = [
            model.bank == request.bank if request.bank is not None else None,
            model.type == request.type if request.type is not None else None,
            model.payment_system == request.payment_system if request.payment_system is not None else None,
            model.is_vip == request.is_vip if request.is_vip is not None else None,
            model.is_active == request.is_active if request.is_active is not None else None,
            model.team_id == request.team_id if request.team_id is not None else None,
            or_(
                func.replace(model.number, "+", "") == search_without_plus,
                model.id == request.search,
                model.name.icontains(request.search),
                model.device_hash.icontains(request.search),
                model.second_number == request.search,
                UserModel.name.ilike(f"%{request.search}%"),
                exists().where(
                    and_(
                        VipPayerModel.bank_detail_id == model.id,
                        VipPayerModel.payer_id == request.search
                    )
                )
            ) if request.search is not None else None,
        ]
        queries = [query for query in queries_none if query is not None]
        return queries

    @classmethod
    async def list(
        cls, session: AsyncSession, namespace_id: int, filter: AdminBankDetailSchemeRequestList
    ) -> BankDetailSchemeResponseList:
        async with get_session(session) as session:
            queries = await cls.get_search_filters(request=filter)
            bank_details_query = (
                select(BankDetailModel, UserModel.name.label("team_name"))
                .join(UserModel, UserModel.id == BankDetailModel.team_id)
                .join(TeamModel, TeamModel.id == BankDetailModel.team_id)
                .where(
                    BankDetailModel.offset_id < filter.last_offset_id,
                    BankDetailModel.is_deleted == False,
                    UserModel.namespace_id == namespace_id,
                    TeamModel.geo_id == filter.geo_id if filter.geo_id is not None else true(),
                    *queries
                )
                .order_by(BankDetailModel.is_active.desc(), BankDetailModel.offset_id.desc())
                .limit(filter.limit)
            )

            results = await session.execute(bank_details_query)
            bank_details = results.fetchall()

            items = []
            for row in bank_details:
                detail = row.BankDetailModel
                team_name = row.team_name
                accepted, closed = await cls.get_transaction_counts(
                    session, detail.id, period_minutes=filter.period
                )
                conv = accepted / (closed + accepted) if (closed + accepted) > 0 else 1.0

                data = detail.__dict__.copy()
                data.pop("today_amount_used", None)
                data.pop("today_transactions_count", None)
                data.pop("period_time", None)

                items.append(
                    AdminBankDetailSchemeResponse(
                        **data,
                        today_amount_used = 0 if detail.last_transaction_timestamp.date() < datetime.datetime.utcnow().date() else detail.today_amount_used,
                        today_transactions_count = 0 if detail.last_transaction_timestamp.date() < datetime.datetime.utcnow().date() else detail.today_transactions_count,
                        team_name=team_name,
                        accepted=accepted,
                        closed=closed,
                        conv=int(conv * 100),
                        period_time=[
                            await time_to_minutes(detail.period_start_time),
                            await time_to_minutes(detail.period_finish_time)
                        ] if detail.period_start_time and detail.period_finish_time else None,
                    )
                )

            items.sort(key=lambda x: (-x.is_active, x.conv, -x.offset_id))

            return BankDetailSchemeResponseList(items=items)

    @classmethod
    async def update(
            cls, session: AsyncSession, detail_id: str, period: int | None, **kwargs
    ) -> AdminBankDetailSchemeResponse | None:
        async with get_session(session) as session:
            logger.info(
                f"[UpdateDetail] - id = {detail_id}, request = {dict(kwargs)}"
            )

            stmt = (
                update(BankDetailModel)
                .where(BankDetailModel.id == detail_id)
                .values(
                    {key: value for key, value in kwargs.items() if value is not None}
                )
            )
            await session.execute(stmt)

            result = await session.execute(
                select(
                    BankDetailModel.profile_id,
                    BankDetailModel.is_vip,
                    BankDetailModel.max_vip_payers,
                ).where(BankDetailModel.id == detail_id)
            )
            row = result.first()

            if row:
                profile_id, is_vip, max_vip_payers = row

                if is_vip:
                    sync_stmt = text("""
                        UPDATE bank_detail_model
                        SET max_vip_payers = :new_max
                        WHERE profile_id = :profile_id
                          AND is_deleted = FALSE
                    """)
                    await session.execute(sync_stmt, {
                        "new_max": max_vip_payers,
                        "profile_id": profile_id
                    })

                elif not is_vip:
                    get_stmt = text("""
                        SELECT max_vip_payers
                        FROM bank_detail_model
                        WHERE profile_id = :profile_id
                          AND is_deleted = FALSE
                        LIMIT 1
                    """)
                    result = await session.execute(get_stmt, {"profile_id": profile_id})
                    max_vip_value = result.scalar_one_or_none()

                    if max_vip_value is not None:
                        await session.execute(
                            update(BankDetailModel)
                            .where(BankDetailModel.id == detail_id)
                            .values(max_vip_payers=max_vip_value)
                        )

            stmt = text("""
                SELECT COUNT(*) 
                FROM vip_payer_model
                WHERE bank_detail_id = :profile_id
            """)
            result = await session.execute(stmt, {"profile_id": profile_id})
            vip_count = result.scalar_one()

            await session.execute(
                update(BankDetailModel)
                .where(BankDetailModel.id == detail_id)
                .values(count_vip_payers=vip_count)
            )

            await session.commit()

            return await cls.get(session=session, detail_id=detail_id, period=period)
