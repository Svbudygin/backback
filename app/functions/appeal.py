import uuid
from base64 import b64encode
from enum import Enum
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_, desc, asc, func, true, update
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status as http_status, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
import logging

from app.enums import TransactionFinalStatusEnum
from app.schemas.AppealScheme import AppealCreateScheme, AppealCloseCodeEnum
from app.core.file_storage import upload_files, download_file, get_file_by_key
from app.core.session import async_session, ro_async_session
from app.core.constants import Role, StatusEnum, Limit, Status
from app.core.constant.appeal_constants import (
    SupportCategoriesEnum,
    TeamCategoriesEnum,
    SUPPORT_CATEGORIES_FILTERS,
    TEAM_CATEGORIES_FILTERS,
)
from app.models import AppealModel, ExternalTransactionModel, MerchantModel, GeoSettingsModel
from app.exceptions import (
    ExternalTransactionNotFoundException,
    UserWrongRoleException,
    NotEnoughPermissionsException,
    UnprocessableEntityException,
    FileNotFoundException
)
from app.schemas.LogsSchema import *
from app.schemas.UserScheme import User
from app.schemas.AppealScheme import (
    AppealMerchantResponseScheme,
    AppealTeamResponseScheme,
    AppealResponseScheme,
    AppealScheme,
    AppealStatusEnum,
    AppealSupportResponseScheme,
    AppealUpdateScheme,
    AppealTeamUpdateScheme,
    AppealSupportUpdateScheme,
    AppealMerchantUpdateScheme,
    AppealListFilterScheme,
    CancelAppealRequestScheme,
    AcceptAppealRequestScheme
)
from app.schemas.CallbackSchema import (
    AppealFinalizationCallbackSchema,
    AppealMerchantStatementRequiredCallbackSchema
)
from app.schemas.PaginationScheme import PaginationParams
from app.core.constant.appeal_constants import (
    SUPPORT_CATEGORIES,
    TEAM_CATEGORIES,
    APPEAL_REJECT_REASONS,
    APPEAL_SUPPORT_REJECT_REASONS,
    APPEAL_REJECT_REASON_TITLES
)
from app.functions.external_transaction import external_transaction_update_
from app.functions.merchant_callback import send_callback
from app.utils.time import calculate_end_time_with_pause
from app.services import notification_service
from app.schemas.NotificationsSchema import NewAppealNotificationSchema, NewAppealNotificationDataSchema
from app.core.config import settings


logger = logging.getLogger(__name__)


class AppealNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Appeal not found", status_code=http_status.HTTP_404_NOT_FOUND)


class StatementTypeEnum(str, Enum):
    MERCHANT = 'is_merchant_statement_required'
    TEAM = 'is_team_statement_required'


UPDATE_SCHEME_BY_ROLE = {
    Role.TEAM: AppealTeamUpdateScheme,
    Role.MERCHANT: AppealMerchantUpdateScheme,
    Role.SUPPORT: AppealSupportUpdateScheme,
}


async def create_appeal(
        current_user: User,
        dto: AppealCreateScheme,
        files: Optional[List[UploadFile]] = None
) -> AppealMerchantResponseScheme:
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        transaction_id = (await session.execute(
            select(ExternalTransactionModel.id)
            .where(
                and_(
                    or_(
                        ExternalTransactionModel.id == dto.transaction_id,
                        ExternalTransactionModel.merchant_transaction_id == dto.transaction_id
                    ),
                    ExternalTransactionModel.merchant_id == current_user.id if current_user.role == Role.MERCHANT else true()
                )
            )
        )).scalar_one_or_none()

        if not transaction_id:
            raise ExternalTransactionNotFoundException()

        file_paths = None
        if files and len(files):
            file_paths = await upload_files(files)

        appeal = AppealModel(
            transaction_id=transaction_id,
            receipts=file_paths,
            amount=dto.amount,
            merchant_appeal_id=dto.merchant_appeal_id,
            finalization_callback_uri=dto.finalization_callback_uri,
            ask_statement_callback_uri=dto.ask_statement_callback_uri
        )

        session.add(appeal)

        await session.commit()

        await session.refresh(appeal)

        log_data = CreateAppealLogSchema(
            request_id=request_id,
            appeal_id=appeal.id,
            amount=dto.amount,
            user_name=current_user.name,
            user_id=current_user.id,
            transaction_id=appeal.transaction_id,
            appeal_team_id=appeal.transaction.team_id
        )

        logger.info(log_data.model_dump_json())

        logger.info(_get_log_string('CreateAppeal', {
            'appeal_id': appeal.id,
            'amount': dto.amount,
            'transaction_id': appeal.transaction_id,
            'appeal_team_id': appeal.transaction.team_id,
        }))

        await notification_service.send_notification(NewAppealNotificationSchema(
            team_id=appeal.transaction.team_id,
            data=NewAppealNotificationDataSchema(
                link=f"{settings.FRONTEND_APPEALS_URL}/{appeal.id}"
            )
        ))

        return await _get_response_by_role(
            Role.MERCHANT,
            AppealScheme.model_validate(appeal),
            session=session
        )


async def get_appeals(
        current_user: User,
        pagination: PaginationParams,
        filters: AppealListFilterScheme,
        category: str,
        async_or_none_session: Optional[AsyncSession] = None,
        only_count: Optional[bool] = False
) -> List[AppealResponseScheme]:
    async with (async_or_none_session or async_session()) as session:
        filter_conditions = []
        role_conditions = []
        category_conditions = []
        order_by = desc(AppealModel.create_timestamp)

        query = select(AppealModel).options(
        joinedload(AppealModel.transaction).joinedload(ExternalTransactionModel.team),
                joinedload(AppealModel.transaction).joinedload(ExternalTransactionModel.merchant),
                joinedload(AppealModel.transaction).joinedload(ExternalTransactionModel.bank_detail),
            )

        query = query.join(AppealModel.transaction).join(MerchantModel, ExternalTransactionModel.merchant_id == MerchantModel.id)

        if filters.direction is not None:
            filter_conditions.append(ExternalTransactionModel.direction == filters.direction)

        if filters.status is not None:
            filter_conditions.append(ExternalTransactionModel.status == filters.status)

        if filters.from_timestamp is not None:
            filter_conditions.append(AppealModel.create_timestamp >= filters.from_timestamp)

        if filters.to_timestamp is not None:
            filter_conditions.append(AppealModel.create_timestamp <= filters.to_timestamp)

        if filters.geo_id is not None:
            filter_conditions.append(MerchantModel.geo_id == filters.geo_id)

        if current_user.role == Role.SUPPORT:
            role_conditions.append(MerchantModel.namespace_id == current_user.namespace.id)

            if category not in SUPPORT_CATEGORIES_FILTERS:
                category = SupportCategoriesEnum.PENDING
            
            if category == SupportCategoriesEnum.PENDING:
                order_by = asc(AppealModel.create_timestamp)

            category_conditions = SUPPORT_CATEGORIES_FILTERS[category]

            if filters.search:
                category_conditions = []
                filter_conditions = [
                    or_(
                        AppealModel.id.ilike(f"{filters.search}"),
                        ExternalTransactionModel.id.ilike(f"{filters.search}"),
                        ExternalTransactionModel.merchant_transaction_id.ilike(f"{filters.search}"),
                    )
                ]

            if filters.team_id:
                filter_conditions.append(ExternalTransactionModel.team_id == filters.team_id)

            if filters.merchant_id:
                filter_conditions.append(ExternalTransactionModel.merchant_id == filters.merchant_id)

        elif current_user.role == Role.TEAM:
            role_conditions.append(ExternalTransactionModel.team_id == current_user.id)

            if category not in TEAM_CATEGORIES_FILTERS:
                category = TeamCategoriesEnum.PENDING
            
            if category == TeamCategoriesEnum.PENDING:
                order_by = asc(AppealModel.create_timestamp)

            category_conditions = TEAM_CATEGORIES_FILTERS[category]

            if filters.search:
                category_conditions = []
                filter_conditions = [
                    or_(
                        AppealModel.id.ilike(f"{filters.search}"),
                        ExternalTransactionModel.id.ilike(f"{filters.search}"),
                        ExternalTransactionModel.merchant_transaction_id.ilike(f"{filters.search}"),
                    )
                ]
        elif current_user.role == Role.MERCHANT:
            role_conditions.append(
                AppealModel.transaction.has(
                    ExternalTransactionModel.merchant_id == current_user.id
                )
            )

        if only_count:
            query = query.where(
                and_(
                    *role_conditions,
                    *category_conditions,
                    *filter_conditions
                )
            )
            count_query = select(func.count()).select_from(query.subquery()).limit(100)
            return (await session.execute(count_query)).scalar()

        query = query.where(
            and_(
                AppealModel.offset_id < pagination.offset,
                *role_conditions,
                *filter_conditions,
                *category_conditions
            )
        ).order_by(order_by).limit(pagination.limit)

        appeals = (await session.execute(query)).scalars().all()

        return [
            await _get_response_by_role(current_user.role, appeal, session=session)
            for appeal in appeals
        ]


async def get_appeal_by_id(appeal_id: str, current_user: User):
    appeal = None

    async with async_session() as session:
        if current_user.role == Role.MERCHANT:
            appeal = await _get_appeal_by_any_id_and_merchant_id(
                session,
                appeal_id,
                current_user.id
            )

        elif current_user.role == Role.TEAM:
            appeal = await _get_appeal_by_id_and_team_id(
                session,
                appeal_id,
                current_user.id
            )

        elif current_user.role == Role.SUPPORT:
            appeal = await _get_appeal_by_id_and_namespace(
                session,
                appeal_id,
                current_user.namespace.id
            )

        if not appeal:
            raise AppealNotFoundException()

        return await _get_response_by_role(current_user.role, appeal, session=session)


async def update_appeal_by_id(
        appeal_id: str,
        dto: AppealUpdateScheme,
        current_user: User
):
    scheme = UPDATE_SCHEME_BY_ROLE[current_user.role]

    if not scheme:
        raise NotEnoughPermissionsException()

    try:
        validated_data = scheme.model_validate(dto)
    except ValidationError:
        raise UnprocessableEntityException()

    async with async_session() as session:
        appeal = None

        if current_user.role == Role.MERCHANT:
            appeal = await _get_appeal_by_any_id_and_merchant_id(session, appeal_id, current_user.id)
        elif current_user.role == Role.TEAM:
            appeal = await _get_appeal_by_id_and_team_id(session, appeal_id, current_user.id)
        elif current_user.role == Role.SUPPORT:
            appeal = await _get_appeal_by_id_and_namespace(session, appeal_id, current_user.namespace.id)
        else:
            raise NotEnoughPermissionsException()

        if not appeal:
            raise AppealNotFoundException()

        update_data = validated_data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == 'amount' and current_user.role == Role.TEAM:
                appeal.is_support_confirmation_required = True

            setattr(appeal, key, value)

        await session.commit()

        await session.refresh(appeal)

        return await _get_response_by_role(
            current_user.role,
            AppealScheme.model_validate(appeal),
            session=session
        )


async def request_merchant_statement(appeal_id: str, current_user: User):
    return await _request_statement(
        appeal_id,
        current_user,
        StatementTypeEnum.MERCHANT
    )


async def request_team_statement(appeal_id: str, current_user: User):
    return await _request_statement(
        appeal_id,
        current_user,
        StatementTypeEnum.TEAM
    )


async def accept_appeal(
        appeal_id: str,
        data: AcceptAppealRequestScheme,
        current_user: User
):
    if current_user.role not in [Role.SUPPORT, Role.TEAM]:
        raise NotEnoughPermissionsException()
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        async with session.begin():
            appeal = await _get_appeal(session, appeal_id, current_user)

            if not appeal:
                raise AppealNotFoundException()

            if data.new_amount:
                appeal.amount = data.new_amount
            else:
                appeal.amount = appeal.transaction.amount

            if appeal.amount != appeal.transaction.amount and current_user.role == Role.TEAM:
                appeal.is_support_confirmation_required = True
                await session.commit()

                log_data = AcceptAppealByTeamNeedSupportConfirmationLogSchema(
                    request_id=request_id,
                    user_name=current_user.name,
                    user_id=current_user.id,
                    appeal_id=appeal.id,
                    transaction_id=appeal.transaction_id,
                    appeal_team_id=appeal.transaction.team_id,
                    appeal_amount=appeal.amount
                )

                logger.info(log_data.model_dump_json())
                logger.info(_get_log_string('AcceptAppealByTeamNeedSupportConfirmation', {
                    'appeal_id': appeal.id,
                    'transaction_id': appeal.transaction_id,
                    'appeal_team_id': appeal.transaction.team_id,
                    'user_name': current_user.name,
                    'appeal_amount': appeal.amount,
                }))
            else:
                appeal.is_support_confirmation_required = False
                appeal.is_merchant_statement_required = False
                appeal.is_team_statement_required = False
                appeal.close_timestamp = func.now()

                await external_transaction_update_(
                    transaction_id=appeal.transaction_id,
                    session=session,
                    status=Status.ACCEPT,
                    new_amount=appeal.amount,
                    final_status=TransactionFinalStatusEnum.APPEAL if appeal.amount == appeal.transaction.amount else TransactionFinalStatusEnum.RECALC
                )

                log_prefix = f"AcceptAppealBy{current_user.role.capitalize()}"

                log_data = AcceptAppealByRoleLogSchema(
                    request_id=request_id,
                    log_name=log_prefix,
                    user_name=current_user.name,
                    user_id=current_user.id,
                    appeal_id=appeal.id,
                    transaction_id=appeal.transaction_id,
                    appeal_team_id=appeal.transaction.team_id,
                    appeal_amount=appeal.amount
                )

                logger.info(log_data.model_dump_json())
                logger.info(_get_log_string(log_prefix, {
                    'appeal_id': appeal.id,
                    'transaction_id': appeal.transaction_id,
                    'appeal_team_id': appeal.transaction.team_id,
                    'user_name': current_user.name,
                    'appeal_amount': appeal.amount,
                }))

        await session.refresh(appeal)

        if not appeal.is_support_confirmation_required and appeal.transaction.status == StatusEnum.ACCEPT:
            await _send_appeal_finalization_callback(
                appeal.transaction.merchant_id,
                request_id,
                AppealStatusEnum.accept,
                AppealScheme.model_validate(appeal)
            )

        return await _get_response_by_role(
            current_user.role,
            AppealScheme.model_validate(appeal),
            session=session
        )


async def cancel_appeal(
        appeal_id: str,
        data: CancelAppealRequestScheme,
        current_user: User
):
    if current_user.role not in [Role.SUPPORT, Role.TEAM]:
        raise NotEnoughPermissionsException()
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        appeal = await _get_appeal(session, appeal_id, current_user)

        if not appeal:
            raise AppealNotFoundException()

        appeal.reject_reason = data.reason

        if current_user.role == Role.TEAM:
            appeal.is_support_confirmation_required = True

            log_data = CancelAppealByTeamNeedSupportConfirmationLogSchema(
                request_id=request_id,
                user_name=current_user.name,
                user_id=current_user.id,
                appeal_id=appeal.id,
                transaction_id=appeal.transaction_id,
                appeal_team_id=appeal.transaction.team_id,
                reject_reason=appeal.reject_reason
            )

            logger.info(log_data.model_dump_json())
            logger.info(_get_log_string('CancelAppealByTeamNeedSupportConfirmation', {
                'appeal_id': appeal.id,
                'transaction_id': appeal.transaction_id,
                'appeal_team_id': appeal.transaction.team_id,
                'user_name': current_user.name,
                'reject_reason': appeal.reject_reason,
            }))
        
        if current_user.role == Role.SUPPORT:
            appeal.is_support_confirmation_required = False
            appeal.close_timestamp = func.now()

            await session.execute(
                update(ExternalTransactionModel)
                .where(ExternalTransactionModel.id == appeal.transaction_id)
                .values(final_status=TransactionFinalStatusEnum.APPEAL)
            )

            log_data = CancelAppealBySupportLogSchema(
                request_id=request_id,
                user_name=current_user.name,
                user_id=current_user.id,
                appeal_id=appeal.id,
                transaction_id=appeal.transaction_id,
                appeal_team_id=appeal.transaction.team_id,
                reject_reason=appeal.reject_reason,
            )

            logger.info(log_data.model_dump_json())

            logger.info(_get_log_string('CancelAppealBySupport', {
                'appeal_id': appeal.id,
                'transaction_id': appeal.transaction_id,
                'appeal_team_id': appeal.transaction.team_id,
                'user_name': current_user.name,
                'reject_reason': appeal.reject_reason,
            }))

        await session.commit()

        await session.refresh(appeal)

        if not appeal.is_support_confirmation_required and appeal.reject_reason is not None:
            await _send_appeal_finalization_callback(
                appeal.transaction.merchant_id,
                request_id,
                AppealStatusEnum.close,
                AppealScheme.model_validate(appeal)
            )

        return await _get_response_by_role(
            current_user.role,
            AppealScheme.model_validate(appeal),
            session=session
        )


async def upload_team_statement(
        appeal_id: str,
        file: UploadFile,
        current_user: User
):
    if current_user.role not in [Role.SUPPORT, Role.TEAM]:
        raise NotEnoughPermissionsException()
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        appeal = await _get_appeal(session, appeal_id, current_user)

        if not appeal:
            raise AppealNotFoundException()

        file_paths = await upload_files([file])

        appeal.team_statements = file_paths
        appeal.is_team_statement_required = False

        await session.commit()

        await session.refresh(appeal)

        log_prefix = f'AppealUploadTeamStatementBy{current_user.role.capitalize()}'
        log_data = AppealUploadTeamStatementByRoleLogSchema(
            request_id=request_id,
            log_name=log_prefix,
            user_name=current_user.name,
            user_id=current_user.id,
            appeal_id=appeal.id,
            transaction_id=appeal.transaction_id,
            appeal_team_id=appeal.transaction.team_id
        )

        logger.info(log_data.model_dump_json())
        logger.info(_get_log_string(log_prefix, {
            'appeal_id': appeal.id,
            'transaction_id': appeal.transaction_id,
            'appeal_team_id': appeal.transaction.team_id,
            'user_name': current_user.name
        }))

        return await _get_response_by_role(
            current_user.role,
            AppealScheme.model_validate(appeal),
            session=session
        )


async def upload_merchant_statement(
        appeal_id: str,
        file: UploadFile,
        current_user: User
):
    if current_user.role not in [Role.SUPPORT, Role.MERCHANT, Role.TG_APPEAL_WORKER]:
        raise NotEnoughPermissionsException()
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        appeal = await _get_appeal(session, appeal_id, current_user)

        if not appeal:
            raise AppealNotFoundException()

        file_paths = await upload_files([file])

        appeal.merchant_statements = file_paths
        appeal.is_merchant_statement_required = False

        await session.commit()

        await session.refresh(appeal)

        log_prefix = f"AppealUploadMerchantStatementBy{current_user.role.capitalize()}"

        log_data = AppealUploadMerchantStatementByRoleLogSchema(
            request_id=request_id,
            log_name=log_prefix,
            user_name=current_user.name,
            user_id=current_user.id,
            appeal_id=appeal.id,
            transaction_id=appeal.transaction_id,
            appeal_team_id=appeal.transaction.team_id
        )

        logger.info(log_data.model_dump_json())
        logger.info(_get_log_string(log_prefix, {
            'appeal_id': appeal.id,
            'transaction_id': appeal.transaction_id,
            'appeal_team_id': appeal.transaction.team_id,
            'user_name': current_user.name
        }))

        return await _get_response_by_role(
            current_user.role,
            AppealScheme.model_validate(appeal),
            session=session
        )


async def download_statement(
        appeal_id: str,
        file_id: str,
        current_user: User
) -> StreamingResponse:
    async with async_session() as session:
        appeal = await _get_appeal(session, appeal_id, current_user)

        if not appeal:
            raise AppealNotFoundException()

        if (
            file_id in (appeal.team_statements or []) or file_id in (appeal.merchant_statements or [])
        ):
            return StreamingResponse(
                download_file(file_id),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename={file_id}"
                }
            )

        raise FileNotFoundException()


async def get_receipts_links(appeal_id: str, current_user: User):
    async with async_session() as session:
        appeal = await _get_appeal(session, appeal_id, current_user)

        if not appeal:
            raise AppealNotFoundException()

        images = []

        for receipt in appeal.receipts or []:
            try:
                image_bytes = await get_file_by_key(receipt)
                base64_str = b64encode(image_bytes).decode("utf-8")

                file_extension = receipt.split('.')[-1].lower()
                if file_extension == 'pdf':
                    mime_type = 'application/pdf'
                elif file_extension == 'png':
                    mime_type = 'image/png'
                elif file_extension in ('jpg', 'jpeg'):
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'application/octet-stream'
                
                images.append(f"data:{mime_type};base64,{base64_str}")
            except FileNotFoundException:
                continue

        return images


async def get_categories(current_user: User, geo_id: Optional[int]):
    if current_user.role == Role.SUPPORT:
        return await modify_categories(
            SUPPORT_CATEGORIES,
            current_user,
            geo_id=geo_id
        )
    elif current_user.role == Role.TEAM:
        return TEAM_CATEGORIES

    raise NotEnoughPermissionsException()


async def modify_categories(
        categories,
        current_user: User,
        existing_session: AsyncSession | None = None,
        geo_id: Optional[int] = None
):
    async with (existing_session or ro_async_session()) as session:
        async def modify_category(category):
            new_category = {
                **category
            }

            if new_category["code"] in [
                SupportCategoriesEnum.NEED_TO_FINALIZE_PENDING,
                SupportCategoriesEnum.NEED_TO_FINALIZE_TEAM_STATEMENT,
                SupportCategoriesEnum.NEED_TO_FINALIZE_MERCHANT_STATEMENT,
                SupportCategoriesEnum.NEED_TO_FINALIZE_TIMEOUT
            ]:
                new_category["count"] = await get_appeals(
                    current_user,
                    pagination=PaginationParams(limit=100, last_offset_id=Limit.MAX_INT),
                    category=new_category["code"],
                    filters=AppealListFilterScheme(
                        geo_id=geo_id,
                    ),
                    async_or_none_session=session,
                    only_count=True
                )

            if "children" in category and isinstance(category["children"], list):
                new_children = []
                for child_row in category["children"]:
                    new_child_row = []
                    for child in child_row:
                        new_child_row.append(await modify_category(child))
                    new_children.append(new_child_row)
                new_category["children"] = new_children

            return new_category

        result = []
        for row in categories:
            new_row = []
            for category in row:
                new_row.append(await modify_category(category))
            result.append(new_row)
        return result


def get_appeal_reject_reasons(current_user: User):
    if current_user.role not in [Role.SUPPORT, Role.TEAM]:
        raise NotEnoughPermissionsException()
    
    lang = "en" if current_user.role == Role.SUPPORT else "ru"
    reasons = APPEAL_SUPPORT_REJECT_REASONS if current_user.role == Role.SUPPORT else APPEAL_REJECT_REASONS

    return [
        {
            "code": reason.value,
            "title": APPEAL_REJECT_REASON_TITLES[reason.value][lang]
        }
        for reason in reasons
        if not getattr(reason, 'is_private', False)
    ]


async def _request_statement(
        appeal_id: str,
        current_user: User,
        statement_type: StatementTypeEnum
):
    request_id = str(uuid.uuid4())
    async with async_session() as session:
        appeal = await _get_appeal(session, appeal_id, current_user)

        if not appeal:
            raise AppealNotFoundException()

        setattr(appeal, statement_type.value, True)

        await session.commit()

        await session.refresh(appeal)

        if statement_type == StatementTypeEnum.TEAM:
            log_prefix = f"AppealRequestTeamStatementBy{current_user.role.capitalize()}"

            log_data = AppealRequestTeamStatementByRoleLogSchema(
                request_id=request_id,
                log_name=log_prefix,
                user_name=current_user.name,
                user_id=current_user.id,
                appeal_id=appeal.id,
                transaction_id=appeal.transaction_id,
                appeal_team_id=appeal.transaction.team_id
            )

            logger.info(log_data.model_dump_json())
            logger.info(_get_log_string(log_prefix, {
                'appeal_id': appeal.id,
                'transaction_id': appeal.transaction_id,
                'appeal_team_id': appeal.transaction.team_id,
                'user_name': current_user.name
            }))

        if statement_type == StatementTypeEnum.MERCHANT:
            log_prefix = f"AppealRequestMerchantStatementBy{current_user.role.capitalize()}"

            log_data = AppealRequestMerchantStatementByRoleLogSchema(
                request_id=request_id,
                log_name=log_prefix,
                user_name=current_user.name,
                user_id=current_user.id,
                appeal_id=appeal.id,
                transaction_id=appeal.transaction_id,
                appeal_team_id=appeal.transaction.team_id
            )

            logger.info(log_data.model_dump_json())
            logger.info(_get_log_string(log_prefix, {
                'appeal_id': appeal.id,
                'transaction_id': appeal.transaction_id,
                'appeal_team_id': appeal.transaction.team_id,
                'user_name': current_user.name
            }))

            await _send_appeal_merchant_statement_callback(
                appeal.transaction.merchant_id,
                request_id,
                AppealScheme.model_validate(appeal)
            )

        return await _get_response_by_role(
            current_user.role,
            AppealScheme.model_validate(appeal),
            session=session
        )


async def _get_appeal(
        session: AsyncSession,
        appeal_id: str,
        current_user: User
):
    if current_user.role == Role.TEAM:
        return await _get_appeal_by_id_and_team_id(
            session,
            appeal_id,
            current_user.id
        )

    elif current_user.role == Role.SUPPORT or current_user.role == Role.TG_APPEAL_WORKER:
        return await _get_appeal_by_id_and_namespace(
            session,
            appeal_id,
            current_user.namespace.id
        )

    elif current_user.role == Role.MERCHANT:
        return await _get_appeal_by_any_id_and_merchant_id(
            session,
            appeal_id,
            current_user.id
        )

    raise UserWrongRoleException(roles=[Role.TEAM, Role.SUPPORT, Role.MERCHANT])


async def _get_appeal_by_id_and_namespace(
        session: AsyncSession,
        appeal_id: str,
        namespace_id: int
):
    return (await session.execute(
        select(AppealModel)
        .join(AppealModel.transaction)
        .join(MerchantModel, ExternalTransactionModel.merchant_id == MerchantModel.id)
        .where(
            and_(
                AppealModel.id == appeal_id,
                MerchantModel.namespace_id == namespace_id
            )
        )
        .options(
            joinedload(AppealModel.transaction, innerjoin=True).joinedload(ExternalTransactionModel.team),
            joinedload(AppealModel.transaction, innerjoin=True).joinedload(ExternalTransactionModel.merchant),
            joinedload(AppealModel.transaction, innerjoin=True).joinedload(ExternalTransactionModel.bank_detail)
        )
        .with_for_update(of=AppealModel)
    )).scalar_one_or_none()


async def _get_appeal_by_any_id_and_merchant_id(
        session: AsyncSession,
        id: str,
        merchant_id: str
):
    return (await session.execute(
        select(AppealModel)
        .join(AppealModel.transaction)
        .where(
            and_(
                or_(
                    AppealModel.id == id,
                    AppealModel.merchant_appeal_id == id,
                    ExternalTransactionModel.id == id,
                    ExternalTransactionModel.merchant_transaction_id == id
                ),
                ExternalTransactionModel.merchant_id == merchant_id
            )
        )
        .options(
            joinedload(AppealModel.transaction).joinedload(ExternalTransactionModel.team),
            joinedload(AppealModel.transaction).joinedload(ExternalTransactionModel.merchant),
            joinedload(AppealModel.transaction).joinedload(ExternalTransactionModel.bank_detail),
        )
    )).scalar_one_or_none()


async def _get_appeal_by_id_and_team_id(
        session: AsyncSession,
        id: str,
        team_id: str
):
    return (await session.execute(
        select(AppealModel)
        .join(AppealModel.transaction)
        .where(
            and_(
                or_(
                    AppealModel.id == id
                ),
                ExternalTransactionModel.team_id == team_id
            )
        )
        .options(
            joinedload(AppealModel.transaction, innerjoin=True).joinedload(ExternalTransactionModel.team),
            joinedload(AppealModel.transaction, innerjoin=True).joinedload(ExternalTransactionModel.merchant),
            joinedload(AppealModel.transaction, innerjoin=True).joinedload(ExternalTransactionModel.bank_detail)
        )
        .with_for_update(of=AppealModel)
    )).scalar_one_or_none()

async def _get_response_by_role(role: str, appeal: AppealScheme, session: Optional[AsyncSession] = None) -> AppealResponseScheme:
    status = AppealStatusEnum.pending

    if appeal.transaction.status == StatusEnum.ACCEPT:
        status = AppealStatusEnum.accept
    elif appeal.reject_reason is not None and not appeal.is_support_confirmation_required:
        status = AppealStatusEnum.close
    elif appeal.is_team_statement_required or appeal.is_merchant_statement_required:
        status = AppealStatusEnum.wait_statement
    
    lang = "en" if role == Role.SUPPORT else "ru"
    raw_reject_reason = appeal.reject_reason
    reject_reason = APPEAL_REJECT_REASON_TITLES.get(appeal.reject_reason, {}).get(lang, None)

    base_data = {
        "id": appeal.id,
        "create_timestamp": appeal.create_timestamp,
        "new_amount": appeal.amount
    }

    appeal_data = appeal.__dict__
    del appeal_data["reject_reason"]

    if role == Role.MERCHANT or role == Role.TG_APPEAL_WORKER:
        if appeal.is_merchant_statement_required:
            status = AppealStatusEnum.wait_merchant_statement

        return AppealMerchantResponseScheme(
            **base_data,
            merchant_appeal_id=appeal.merchant_appeal_id,
            merchant_transaction_id=appeal.transaction.merchant_transaction_id,
            status=status,
            code=raw_reject_reason,
            comment=appeal.reject_comment
        )

    elif role == Role.TEAM:
        del base_data["id"]
        del base_data["create_timestamp"]

        auto_accept_timestamp = None

        if appeal_data.get("team_processing_start_time") and session:
            settings = (await session.execute(
                select(
                    GeoSettingsModel.is_auto_accept_appeals_enabled,
                    GeoSettingsModel.auto_accept_appeals_downtime_s,
                    GeoSettingsModel.auto_accept_appeals_pause_time_from,
                    GeoSettingsModel.auto_accept_appeals_pause_time_to
                )
                .where(GeoSettingsModel.id == appeal.transaction.merchant.geo_id)
            )).first()

            if settings.is_auto_accept_appeals_enabled and settings.auto_accept_appeals_downtime_s:
                auto_accept_timestamp = calculate_end_time_with_pause(
                    appeal_data.get("team_processing_start_time"),
                    settings.auto_accept_appeals_downtime_s,
                    settings.auto_accept_appeals_pause_time_from,
                    settings.auto_accept_appeals_pause_time_to
                )

        return AppealTeamResponseScheme(
            **base_data,
            **appeal_data,
            status=status,
            reject_reason=reject_reason,
            auto_accept_timestamp=auto_accept_timestamp
        )

    else: # SUPPORT
        del base_data["id"]
        del base_data["create_timestamp"]

        auto_accept_timestamp = None

        if appeal_data.get("team_processing_start_time") and session:
            settings = (await session.execute(
                select(
                    GeoSettingsModel.is_auto_accept_appeals_enabled,
                    GeoSettingsModel.auto_accept_appeals_downtime_s,
                    GeoSettingsModel.auto_accept_appeals_pause_time_from,
                    GeoSettingsModel.auto_accept_appeals_pause_time_to
                )
                .where(GeoSettingsModel.id == appeal.transaction.merchant.geo_id)
            )).first()

            if settings.is_auto_accept_appeals_enabled and settings.auto_accept_appeals_downtime_s:
                auto_accept_timestamp = calculate_end_time_with_pause(
                    appeal_data.get("team_processing_start_time"),
                    settings.auto_accept_appeals_downtime_s,
                    settings.auto_accept_appeals_pause_time_from,
                    settings.auto_accept_appeals_pause_time_to
                )

        return AppealSupportResponseScheme(
            **base_data,
            **appeal_data,
            status=status,
            reject_reason=reject_reason,
            auto_accept_timestamp=auto_accept_timestamp
        )


def _remove_filters(input_array):
    return [
        list(map(lambda x: {k: x[k] for k in x if k != 'filters'}, subarray))
        for subarray in input_array
    ]


async def _send_appeal_merchant_statement_callback(merchant_id: str, request_id: str, appeal: AppealScheme):
    if not appeal.ask_statement_callback_uri:
        return

    await send_callback(
        appeal.ask_statement_callback_uri,
        merchant_id,
        request_id,
        AppealMerchantStatementRequiredCallbackSchema(
            id=appeal.id,
            transaction_id=appeal.transaction.id,
            merchant_transaction_id=appeal.transaction.merchant_transaction_id,
            merchant_appeal_id=appeal.merchant_appeal_id
        )
    )


async def get_pending_count(session: AsyncSession, current_user: User):
    appeals_count = len(await get_appeals(
        current_user,
        pagination=PaginationParams(limit=100, last_offset_id=Limit.MAX_INT),
        category=TeamCategoriesEnum.PENDING,
        filters=AppealListFilterScheme(),
        async_or_none_session=session
    ))

    return appeals_count


async def _send_appeal_finalization_callback(
        merchant_id: str,
        request_id: str,
        status: AppealStatusEnum,
        appeal: AppealScheme
):
    if not appeal.finalization_callback_uri:
        return

    await send_callback(
        appeal.finalization_callback_uri,
        merchant_id,
        request_id,
        AppealFinalizationCallbackSchema(
            id=appeal.id,
            transaction_id=appeal.transaction.id,
            merchant_transaction_id=appeal.transaction.merchant_transaction_id,
            merchant_appeal_id=appeal.merchant_appeal_id,
            new_amount=appeal.amount or appeal.transaction.amount,
            status=status.value,
            code=appeal.reject_reason
        )
    )


async def accept_appeal_by_system(session: AsyncSession, appeal_id: str):
    appeal = (await session.execute(
        select(AppealModel)
        .where(AppealModel.id == appeal_id)
    )).scalar_one_or_none()

    if not appeal:
        raise AppealNotFoundException()

    appeal.timeout_expired = True

    await session.commit()


def _get_log_string(prefix, data):
    items = [f"{k} = {v}" for k, v in data.items()]
    utc_time = datetime.utcnow()
    return f"[{prefix}] - " + ", ".join(items) + f", UTC_time = {utc_time}"
