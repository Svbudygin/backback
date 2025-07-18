from sqlalchemy import select, update
from typing import List

from app.core.session import ro_async_session
from app.models import RoleModel, PermissionModel
from app.schemas.RoleScheme import (
    RoleScheme, CreateRoleScheme, UpdateRoleScheme, PermissionScheme
)


async def get_roles() -> List[RoleModel]:
    async with (ro_async_session() as session):
        return (
            await session.execute(
                select(RoleModel)
                .order_by(RoleModel.name)
            )
        ).scalars().all()


async def create_role(create_role_dto: CreateRoleScheme) -> RoleScheme:
    async with (ro_async_session() as session):
        role = RoleModel(name=create_role_dto.name)

        if create_role_dto.permissions:
            permissions = await session.execute(
                select(PermissionModel)
                .filter(PermissionModel.id.in_(create_role_dto.permissions))
            )
            permissions = permissions.scalars().all()
            role.permissions.extend(permissions)

        session.add(role)
        await session.commit()

        await session.refresh(role)

        return RoleScheme(**role.__dict__)


async def update_role(
        role_id: int,
        update_role_dto: UpdateRoleScheme
) -> RoleScheme:
    async with ro_async_session() as session:
        await session.execute(
            update(RoleModel)
            .where(RoleModel.id == role_id)
            .values(name=update_role_dto.name)
        )

        if update_role_dto.permissions is not None:
            role = await session.get(RoleModel, role_id)

            if role:
                role.permissions.clear()
                permissions = await session.execute(
                    select(PermissionModel)
                    .filter(PermissionModel.id.in_(update_role_dto.permissions))
                )
                permissions = permissions.scalars().all()
                role.permissions.extend(permissions)

        await session.commit()

        role = await session.get(RoleModel, role_id)
        await session.refresh(role)

        return role


async def get_permissions() -> List[PermissionScheme]:
    async with (ro_async_session() as session):
        return (
            await session.execute(
                select(PermissionModel)
                .order_by(PermissionModel.code)
            )
        ).scalars().all()
