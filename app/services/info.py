from app.core.session import ro_async_session
from app.exceptions import NotEnoughPermissionsException
from app.schemas.UserScheme import User
from app.schemas.InfoSchema import InfoSummaryResponseSchema
from app.core.constants import Role
from app.functions.appeal import get_pending_count
from app.functions.external_transaction import get_team_pending_pay_outs_count, get_available_pay_outs_for_team_count


async def get_summary(user: User):
    if user.role not in [Role.TEAM]:
        raise NotEnoughPermissionsException()

    async with ro_async_session() as session:
        return InfoSummaryResponseSchema(
            pending_appeals=(await get_pending_count(session, user)),
            pending_pay_outs=(await get_team_pending_pay_outs_count(session, user.id)),
            total_pay_outs=(await get_available_pay_outs_for_team_count(session, user))
        )
