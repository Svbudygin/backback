from typing import Dict, List, Tuple

from app.functions.admin.base_services import (
    validate_unique_user,
    validate_user_has_role,
)

from app.core.constants import Role
from app.models import UserModel, SupportModel, AccessMatrix
from app.core.security import generate_password, get_password_hash
from app.repositories.admin.support_repo import SupportRepo
from app.schemas.admin.SupportScheme import SupportResponseScheme, CreateSupportRequestScheme, V2SupportResponseScheme
from app.utils.session import get_session


async def create_support_user(
        session,
        name: str,
        namespace_id: int,
        view_traffic: bool = False,
        view_fee: bool = False,
        view_pay_in: bool = False,
        view_pay_out: bool = False,
        view_teams: bool = False,
        view_merchants: bool = False,
        view_agents: bool = False,
        view_wallet: bool = False,
        view_supports: bool = False,
        view_search: bool = False,
        view_compensations: bool = False,
        view_sms_hub: bool = False,
        view_accounting: bool = False,
        view_details: bool = False,
        view_appeals: bool = False,
        view_analytics: bool = False
) -> Tuple[UserModel, Dict]:
    async with get_session(session) as session:
        password = generate_password()

        support_model = SupportModel(
            password_hash=get_password_hash(password),
            name=name,
            role=Role.SUPPORT,
            is_blocked=False,
            namespace_id=namespace_id,
        )

        session.add(support_model)
        await session.flush()

        access_model: AccessMatrix = AccessMatrix(
            user_id=support_model.id,
            view_traffic=view_traffic,
            view_fee=view_fee,
            view_pay_in=view_pay_in,
            view_pay_out=view_pay_out,
            view_teams=view_teams,
            view_merchants=view_merchants,
            view_agents=view_agents,
            view_wallet=view_wallet,
            view_supports=view_supports,
            view_search=view_search,
            view_compensations=view_compensations,
            view_sms_hub=view_sms_hub,
            view_accounting=view_accounting,
            view_details=view_details,
            view_appeals=view_appeals,
            view_analytics=view_analytics,
        )

        session.add(access_model)

        await session.flush()
        return support_model, {"password": password}


async def create_and_get_support_user(
        session,
        request: CreateSupportRequestScheme,
        namespace_id: int
):
    async with get_session(session) as session:
        async with session.begin():
            name = request.name
            await validate_unique_user(session, name=name, namespace_id=namespace_id)
            user, credentials = await create_support_user(
                session,
                name=name,
                view_traffic=request.view_traffic,
                view_fee=request.view_fee,
                view_pay_in=request.view_pay_in,
                view_pay_out=request.view_pay_out,
                view_teams=request.view_teams,
                view_merchants=request.view_merchants,
                view_agents=request.view_agents,
                view_wallet=request.view_wallet,
                view_supports=request.view_supports,
                view_search=request.view_search,
                view_compensations=request.view_compensations,
                view_sms_hub=request.view_sms_hub,
                view_accounting=request.view_accounting,
                view_details=request.view_details,
                view_appeals=request.view_appeals,
                view_analytics=request.view_analytics,
                namespace_id=namespace_id
            )

            support_user: V2SupportResponseScheme = await SupportRepo.get(
                session,
                support_id=user.id
            )

            update = {
                **credentials
            }

            support_user = support_user.model_copy(update=update)

            await session.commit()

            return support_user


async def list_support_users(
    namespace_id: int,
    session=None
) -> List[V2SupportResponseScheme]:
    async with get_session(session) as session:
        users: List[V2SupportResponseScheme] = await SupportRepo.list(
            session=session,
            namespace_id=namespace_id
        )
        return users


async def update_support_user(session=None, **kwargs) -> V2SupportResponseScheme:
    async with get_session(session) as session:
        await validate_user_has_role(
            session=session, user_id=kwargs["user_id"], role=kwargs["role"]
        )
        user = await SupportRepo.update(session=session, **kwargs)
        return user
