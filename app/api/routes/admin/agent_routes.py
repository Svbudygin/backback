from typing import List

from fastapi import APIRouter, Depends

from app import exceptions
from app.api.deps import v2_get_current_support_user
from app.core.constants import Role
from app.functions.admin.agent_services import (
    list_agent_users,
    create_and_get_agent_user,
    update_agent_user,
    regenerate_agent_user
)
from app.schemas.GenericScheme import GenericListResponse
from app.schemas.admin.AgentScheme import (
    AgentResponseScheme,
    CreateAgentRequestScheme,
    UpdateAgentRequestScheme,
    V2AgentResponseScheme
)
from app.schemas.UserScheme import AdminUserSchemeResponse, UserSupportScheme

router = APIRouter()


@router.post("/")
async def create(
    request: CreateAgentRequestScheme,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> V2AgentResponseScheme:
    agent: V2AgentResponseScheme = await create_and_get_agent_user(
        None,
        name=request.name,
        namespace_id=current_user.namespace.id
    )
    return agent


@router.get("/")
async def list(
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> GenericListResponse[V2AgentResponseScheme]:
    agents: List[V2AgentResponseScheme] = await list_agent_users(
        namespace_id=current_user.namespace.id
    )
    return GenericListResponse(items=agents)


@router.patch("/{id}")
async def update(
    id: str,
    request: UpdateAgentRequestScheme,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> V2AgentResponseScheme:
    data = request.model_dump(exclude_unset=True)
    agent: V2AgentResponseScheme = await update_agent_user(
        user_id=id, role=Role.AGENT, **data
    )
    return agent


@router.patch("/regenerate/{id}")
async def regenerate(
    id: str,
    current_user=Depends(v2_get_current_support_user),
) -> V2AgentResponseScheme:
    if current_user.role != Role.SUPPORT:
        raise exceptions.UserWrongRoleException(roles=[Role.SUPPORT])

    agent_user: V2AgentResponseScheme = await regenerate_agent_user(
        agent_id=id
    )

    return agent_user
