from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role
from app.models import UserModel, AccessMatrix, SupportModel
from app.schemas.admin.SupportScheme import SupportResponseScheme, V2SupportResponseScheme
from app.utils.session import get_session


class SupportRepo:
    @classmethod
    async def get(
            cls, session: AsyncSession, support_id: str
    ) -> V2SupportResponseScheme | None:
        async with get_session(session) as session:
            query = (
                select(SupportModel)
                .filter(
                    SupportModel.id == support_id
                )
            )

            result = await session.execute(query)
            user_row = result.scalar_one_or_none()

            if not user_row:
                return None

            access_query = select(
                AccessMatrix
            ).where(AccessMatrix.user_id == user_row.id)

            access_result = await session.execute(access_query)
            access_data = access_result.scalar_one_or_none()

            if not access_data:
                return V2SupportResponseScheme.model_validate(user_row)

            data = {
                **access_data.__dict__,
                **user_row.__dict__
            }

            return V2SupportResponseScheme.model_validate(data)

    @classmethod
    async def list(
        cls, session: AsyncSession, namespace_id: int
    ) -> List[V2SupportResponseScheme]:
        async with get_session(session) as session:
            stmt = (
                select(UserModel)
                .where(
                    UserModel.role == Role.SUPPORT
                )
                .where(
                    UserModel.namespace_id == namespace_id
                )
            )

            result = await session.execute(stmt)
            user_rows = result.scalars().all()

            access_query = select(
                AccessMatrix.user_id,
                AccessMatrix.view_supports,
                AccessMatrix.view_fee,
                AccessMatrix.view_teams,
                AccessMatrix.view_agents,
                AccessMatrix.view_search,
                AccessMatrix.view_compensations,
                AccessMatrix.view_merchants,
                AccessMatrix.view_pay_in,
                AccessMatrix.view_pay_out,
                AccessMatrix.view_traffic,
                AccessMatrix.view_wallet,
                AccessMatrix.view_accounting,
                AccessMatrix.view_sms_hub,
                AccessMatrix.view_details,
                AccessMatrix.view_appeals,
                AccessMatrix.view_analytics
            ).where(
                AccessMatrix.user_id.in_(
                    [r.id for r in user_rows]
                )
            )

            access_result = await session.execute(access_query)
            access = {r.user_id: r for r in access_result.fetchall()}

            results = []
            for row in user_rows:
                if row is None:
                    continue
                access_data = access.get(row.id)
                if access_data is None:
                    results.append(V2SupportResponseScheme.model_validate(data))
                    continue

                data = {
                    **access_data._asdict(),
                    **row.__dict__
                }

                results.append(V2SupportResponseScheme.model_validate(data))

            return results

    @classmethod
    async def update(cls, *, session: AsyncSession = None, user_id: str, **kwargs):
        user_model_fields = {key: value for key, value in kwargs.items() if hasattr(UserModel, key)}
        access_matrix_fields = {key: value for key, value in kwargs.items() if hasattr(AccessMatrix, key)}

        async with get_session(session) as session:
            if user_model_fields:
                user_stmt = (
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(user_model_fields)
                )
                await session.execute(user_stmt)

            if access_matrix_fields:
                access_stmt = (
                    update(AccessMatrix)
                    .where(AccessMatrix.user_id == user_id)
                    .values(access_matrix_fields)
                )
                await session.execute(access_stmt)

            await session.commit()

            return await cls.get(session=session, support_id=user_id)
