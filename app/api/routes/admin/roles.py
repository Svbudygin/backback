from fastapi import APIRouter, Depends

from app.schemas.GenericScheme import GenericListResponseWithTypes
from app.schemas.RoleScheme import (
    RoleScheme, CreateRoleScheme, UpdateRoleScheme, PermissionScheme
)
import app.services.roles_service as roles_service
from app.api import deps

router = APIRouter()


@router.get("/", dependencies=[Depends(deps.get_support_user)])
async def get_roles() -> GenericListResponseWithTypes[RoleScheme]:
    roles = await roles_service.get_roles()
    return GenericListResponseWithTypes(types = [""], items=roles)


@router.post("/", dependencies=[Depends(deps.get_support_user)])
async def create_role(create_role_dto: CreateRoleScheme) -> RoleScheme:
    return await roles_service.create_role(create_role_dto)


@router.patch("/{role_id}", dependencies=[Depends(deps.get_support_user)])
async def update_role(
        role_id: int,
        update_role_dto: UpdateRoleScheme
) -> RoleScheme:
    return await roles_service.update_role(role_id, update_role_dto)


@router.get("/permissions", dependencies=[Depends(deps.get_support_user)])
async def get_permissions() -> GenericListResponseWithTypes[PermissionScheme]:
    permissions = await roles_service.get_permissions()
    return GenericListResponseWithTypes(types=[""], items=permissions)
