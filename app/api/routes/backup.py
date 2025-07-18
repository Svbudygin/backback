from fastapi import APIRouter, Depends, status

from app import exceptions
from app.api import deps
from app.core.constants import Role
from app.functions.backup import replace_ids
from app.schemas.UserScheme import *

router = APIRouter()


@router.put("/backup")
async def create_team_route(
        current_user: UserSchemeResponse = Depends(deps.get_current_user),
) -> int:
    if current_user.role != Role.ROOT:
        raise exceptions.UserWrongRoleException(roles=[Role.ROOT])
    
    await replace_ids()
    return status.HTTP_200_OK
