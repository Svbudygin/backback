from typing import List
from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user
from app.core.constants import Role
from app.functions.admin.support_services import (
    list_support_users,
    create_and_get_support_user,
    update_support_user
)
from app.schemas.GenericScheme import GenericListResponseWithTypes
from app.schemas.admin.SupportScheme import (
    CreateSupportRequestScheme,
    UpdateSupportRequestScheme,
    V2SupportResponseScheme
)
from app.schemas.UserScheme import UserSupportScheme

router = APIRouter()


@router.post("/")
async def create(
    request: CreateSupportRequestScheme,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> V2SupportResponseScheme:
    support: V2SupportResponseScheme = await create_and_get_support_user(
        None,
        request=request,
        namespace_id=current_user.namespace.id
    )

    return support


@router.get("/")
async def list(
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> GenericListResponseWithTypes[V2SupportResponseScheme]:
    supports: List[V2SupportResponseScheme] = await list_support_users(
        namespace_id=current_user.namespace.id
    )

    return GenericListResponseWithTypes(items=supports)


@router.patch("/{id}")
async def update(
    id: str,
    request: UpdateSupportRequestScheme,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> V2SupportResponseScheme:
    data = request.model_dump(exclude_unset=True)
    support: V2SupportResponseScheme = await update_support_user(
        user_id=id, role=Role.SUPPORT, **data
    )
    return support
