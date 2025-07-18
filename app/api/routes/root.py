from fastapi import APIRouter, Depends, status
from starlette.responses import JSONResponse

from app import exceptions
from app.api import deps
from app.api.deps import v2_get_current_user
from app.core.constants import Role
from app.functions.auto_close_transactions import auto_close_transactions
from app.functions.user import (
    create_agent,
    create_merchant,
    create_support,
    create_team,
)
from app.schemas.UserScheme import *

router = APIRouter()


@router.post("/team")
async def create_team_route(
    name_scheme: UserSchemeRequestCreateTeam,
    current_user: User = Depends(v2_get_current_user),
) -> UserSchemeResponseCreateTeam:
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])

    user = await create_team(
        UserSchemeRequestCreateTeam(
            wallet_id=name_scheme.wallet_id,
            namespace=name_scheme.namespace,
            name=name_scheme.name,
            telegram_bot_secret=name_scheme.telegram_bot_secret,
            telegram_verifier_chat_id=name_scheme.telegram_verifier_chat_id,
            economic_model=name_scheme.economic_model,
            currency_id=name_scheme.currency_id,
            credit_factor=name_scheme.credit_factor,
        )
    )
    """Enable current user"""
    return UserSchemeResponseCreateTeam(**user.__dict__)


@router.post("/merchant")
async def create_team_route(
    merchant_scheme: UserSchemeRequestCreateMerchant,
    current_user: User = Depends(v2_get_current_user),
) -> UserSchemeResponseCreateMerchant:
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])

    user = await create_merchant(
        UserSchemeRequestCreateMerchant(
            wallet_id=merchant_scheme.wallet_id,
            namespace=merchant_scheme.namespace,
            name=merchant_scheme.name,
            telegram_bot_secret=None,
            telegram_verifier_chat_id=None,
            economic_model=merchant_scheme.economic_model,
            currency_id=merchant_scheme.currency_id,
            credit_factor=merchant_scheme.credit_factor,
        )
    )
    """Enable current user"""
    return UserSchemeResponseCreateMerchant(**user.__dict__)


@router.post("/agent")
async def create_agent_route(
    name_scheme: UserSchemeRequestCreateAgent,
    current_user: User = Depends(v2_get_current_user),
) -> UserSchemeResponseCreateAgent:
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])

    user = await create_agent(
        UserSchemeRequestCreateAgent(
            wallet_id=name_scheme.wallet_id,
            namespace=name_scheme.namespace,
            name=name_scheme.name,
            telegram_bot_secret=None,
            telegram_verifier_chat_id=None,
        )
    )
    """Enable current user"""
    return UserSchemeResponseCreateAgent(**user.__dict__)


@router.post("/support")
async def create_support_route(
    request: UserSchemeRequestCreateSupport,
    current_user: User = Depends(v2_get_current_user),
) -> UserSchemeResponseCreateSupport:
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])

    response: UserSchemeResponseCreateSupport = await create_support(request)

    return response


@router.put("/auto-close-transactions")
async def auto_close_transactions_route(
    current_user: User = Depends(v2_get_current_user),
):
    if current_user.role not in (Role.ROOT, Role.TC_WORKER):
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT, Role.TC_WORKER])

    await auto_close_transactions()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "success"})
