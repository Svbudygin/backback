from typing import List
from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user
from app.repositories.admin.admin_repository import (
    filter_users_in_namespace_repo,
)
from app.schemas.GenericScheme import GenericListResponseWithTypes
from app.schemas.UserScheme import UserSupportScheme, User, UserMerchantWithTypeResponseScheme

router = APIRouter()


@router.get("/users")
async def list_users_in_namespace(
    geo_id: int | None = None,
    role: str | None = None,
    current_user: UserSupportScheme = Depends(v2_get_current_support_user),
) -> GenericListResponseWithTypes[UserMerchantWithTypeResponseScheme] | GenericListResponseWithTypes[User]:
    users = await filter_users_in_namespace_repo(
        geo_id=geo_id,
        role=role,
        namespace_id=current_user.namespace.id
    )

    return GenericListResponseWithTypes(items=users)
