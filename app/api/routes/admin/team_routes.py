from typing import List

from fastapi import APIRouter, Depends

from app import exceptions
from app.api.deps import v2_get_current_support_user
from app.core.constants import Role, Limit
from app.functions.admin.team_service import (
    create_and_get_team_user,
    list_team_users,
    update_team_user,
    list_users_balance_info,
    regenerate_team_user
)
from app.schemas.GenericScheme import GenericListResponseWithTypes, GenericListResponse
from app.schemas.admin.TeamScheme import (
    CreateTeamRequestScheme,
    UpdateTeamRequestScheme,
    InfoBalanceScheme,
    V2TeamResponseScheme
)
from app.schemas.UserScheme import UserSupportScheme

router = APIRouter()


@router.post("/")
async def create(
    request: CreateTeamRequestScheme,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> V2TeamResponseScheme:
    team_user: V2TeamResponseScheme = await create_and_get_team_user(
        None,
        name=request.name,
        namespace_id=current_user.namespace.id,
        credit_factor=request.limit,
        balance_id=request.balance_id,
        geo_id=request.geo_id
    )
    return team_user


@router.get("/")
async def list(
    geo_id: int | None = None,
    limit: int = 10,
    last_offset_id: int = Limit.MAX_INT,
    search: str | None = None,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> GenericListResponse[V2TeamResponseScheme]:
    team_users: List[V2TeamResponseScheme] = await list_team_users(
        geo_id=geo_id, namespace_id=current_user.namespace.id, limit=limit, last_offset_id=last_offset_id, search=search
    )
    return GenericListResponse(items=team_users)


@router.get("/balances")
async def list_balances(
    geo_id: int | None = None,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> List[InfoBalanceScheme]:
    team_users: List[InfoBalanceScheme] = await list_users_balance_info(
        geo_id=geo_id, namespace_id=current_user.namespace.id, role=Role.TEAM
    )
    return team_users


@router.patch("/{id}")
async def update(
    id: str,
    request: UpdateTeamRequestScheme,
    current_user=Depends(v2_get_current_support_user),
) -> V2TeamResponseScheme:
    data = request.model_dump(exclude_unset=True)
    team_user: V2TeamResponseScheme = await update_team_user(
        user_id=id, **data
    )

    return team_user

@router.patch("/regenerate/{id}")
async def regenerate(
    id: str,
    current_user=Depends(v2_get_current_support_user),
) -> V2TeamResponseScheme:
    if current_user.role != Role.SUPPORT:
        raise exceptions.UserWrongRoleException(roles=[Role.SUPPORT])

    team_user: V2TeamResponseScheme = await regenerate_team_user(
        team_id=id
    )

    return team_user

