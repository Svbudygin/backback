from typing import Dict, List, Tuple

from app.functions.admin.base_services import (
    validate_unique_user,
    validate_user_has_role,
)

from app.functions.balance import add_balance_changes, get_balances
from app.core.constants import Role
from app.models import UserModel
from app.core.security import generate_password, get_password_hash
from app.repositories.admin.detail_repo import DetailRepo
from app.schemas.admin.DetailsScheme import *
from app.utils.session import get_session, async_session
from sqlalchemy import select
from app.services.notification_service import send_notification
from app.schemas.NotificationsSchema import EnableReqForFillSupportNotificationSchema, DisableReqForFillSupportNotificationSchema, ReqDisabledNotificationDataSchema


async def list_bank_details(
    *, session=None, namespace_id: int, filter: AdminBankDetailSchemeRequestList
) -> BankDetailSchemeResponseList:
    async with get_session(session) as session:
        details: BankDetailSchemeResponseList = await DetailRepo.list(
            session=session, namespace_id=namespace_id, filter=filter
        )
        return details


async def update_bank_details(session=None, **kwargs) -> AdminBankDetailSchemeResponse:
    async with get_session(session) as session:
        request = dict(kwargs)
        was_detail: AdminBankDetailSchemeResponse = await DetailRepo.get(session=session, detail_id=request["detail_id"], period=request["period"])
        detail: AdminBankDetailSchemeResponse = await DetailRepo.update(session=session, **kwargs)
        if detail.fiat_min_inbound < 1000 and detail.is_active == True and (was_detail.is_active == False or was_detail.fiat_min_inbound >= 1000):
            await send_notification(EnableReqForFillSupportNotificationSchema(
                support_id="all",
                data=ReqDisabledNotificationDataSchema(
                    number=detail.number
                )
            ))
        if (detail.fiat_min_inbound >= 1000 or detail.is_active == False) and was_detail.is_active == True and was_detail.fiat_min_inbound < 1000:
            await send_notification(DisableReqForFillSupportNotificationSchema(
                support_id="all",
                data=ReqDisabledNotificationDataSchema(
                    number=detail.number
                )
            ))

        return detail