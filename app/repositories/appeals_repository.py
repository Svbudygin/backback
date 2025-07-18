from datetime import datetime
from typing import List

from sqlalchemy import asc, desc, or_
from sqlalchemy.future import select
from sqlalchemy.orm import aliased

from app.core.constants import Role
from app.core.session import async_session
from app.models import AppealModel, ExternalTransactionModel
from app.schemas.AppealScheme import AppealAPIResponse, AppealListRequest


class AppealRepository:
    async def list_appeals(self, request: AppealListRequest) -> List[AppealAPIResponse]:
        async with async_session() as session:
            transaction_alias = aliased(ExternalTransactionModel)
            query = (
                select(
                    AppealModel.id,
                    AppealModel.transaction_id,
                    transaction_alias.merchant_transaction_id,
                    transaction_alias.exchange_rate,
                    AppealModel.create_timestamp,
                    AppealModel.status,
                    transaction_alias.amount,
                    AppealModel.amount.label("new_amount"),
                    transaction_alias.bank_detail_number,
                    transaction_alias.bank_detail_bank,
                    transaction_alias.bank_detail_name,
                    AppealModel.invoice_file_uri,
                    AppealModel.is_confirmed,
                    AppealModel.offset_id,
                    transaction_alias.direction,
                )
                .join(
                    transaction_alias,
                    AppealModel.transaction_id == transaction_alias.id,
                )
                .limit(request.limit)
            )

            # Пагинация
            if request.last_offset_id:
                query = query.where(AppealModel.offset_id > request.last_offset_id)

            # Фильтрация по роли
            if request.role == Role.MERCHANT:
                query = query.where(transaction_alias.merchant_id == request.user_id)
            elif request.role == Role.TEAM:
                query = query.where(transaction_alias.team_id == request.user_id)

            # Фильтрация по direction
            if request.direction:
                query = query.where(transaction_alias.direction == request.direction)

            # Фильтрация по timestamp
            if request.create_timestamp_from is not None:
                create_timestamp_from = datetime.fromtimestamp(
                    request.create_timestamp_from
                )
                query = query.where(
                    AppealModel.create_timestamp >= create_timestamp_from
                )
            if request.create_timestamp_to is not None:
                create_timestamp_to = datetime.fromtimestamp(
                    request.create_timestamp_to
                )
                query = query.where(AppealModel.create_timestamp <= create_timestamp_to)

            # Фильтрация по статусу
            if request.status:
                query = query.where(AppealModel.status == request.status)

            # Поиск по search
            if request.search:
                subquery = (
                    select(transaction_alias.id)
                    .where(
                        or_(
                            transaction_alias.merchant_transaction_id == request.search,
                            transaction_alias.bank_detail_number == request.search,
                            transaction_alias.bank_detail_bank == request.search,
                            transaction_alias.bank_detail_name == request.search,
                        )
                    )
                    .subquery()
                )
                query = query.where(
                    or_(
                        AppealModel.id == request.search,
                        AppealModel.transaction_id == request.search,
                        AppealModel.transaction_id.in_(subquery),
                    )
                )

            # Сортировка по статусу
            if request.status == "pending":
                query = query.order_by(asc(AppealModel.create_timestamp))
            else:
                query = query.order_by(desc(AppealModel.create_timestamp))

            result = await session.execute(query)
            rows = result.all()

            response = []
            for row in rows:
                response.append(
                    AppealAPIResponse(
                        id=row.id,
                        transaction_id=row.transaction_id,
                        merchant_transaction_id=row.merchant_transaction_id,
                        exchange_rate=row.exchange_rate,
                        create_timestamp=row.create_timestamp,
                        status=row.status,
                        amount=row.amount,
                        new_amount=row.new_amount,
                        bank_detail_number=row.bank_detail_number,
                        bank_detail_bank=row.bank_detail_bank,
                        bank_detail_name=row.bank_detail_name,
                        invoice_file_uri=row.invoice_file_uri,
                        is_confirmed=row.is_confirmed,
                        offset_id=row.offset_id,
                        direction=row.direction,
                    )
                )

            return response
