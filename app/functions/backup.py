from sqlalchemy import select, update, text

from app.core.session import async_session
from app.models import UserBalanceChangeModel, UserBalanceChangeNonceModel


async def replace_ids():
    async with async_session() as session:
        await session.execute(text(
            """LOCK user_balance_change_model, user_balance_change_nonce_model IN ACCESS EXCLUSIVE MODE;"""
        ))
        nonce_user_id_q = await session.execute(
            select(UserBalanceChangeNonceModel.user_id,
                   UserBalanceChangeNonceModel.change_id).distinct()
        )
        nonce_user_id_list = []
        nonce_user_id_set = set()
        for user_id_list, nonce in nonce_user_id_q:
            nonce_user_id_list.append((user_id_list, nonce))
            nonce_user_id_set.add(user_id_list)
        print(nonce_user_id_list)
        for user_id_list, nonce in nonce_user_id_list:
            await session.execute(
                update(UserBalanceChangeModel)
                .filter(UserBalanceChangeModel.user_id == user_id_list,
                        UserBalanceChangeModel.id <= nonce)
                .values(id=-1)
            )
            await session.execute(
                update(UserBalanceChangeModel)
                .filter(UserBalanceChangeModel.user_id == user_id_list,
                        UserBalanceChangeModel.id > nonce)
                .values(id=0))
            await session.execute(
                update(UserBalanceChangeNonceModel)
                .filter(UserBalanceChangeNonceModel.user_id == user_id_list)
                .values(change_id=0))
        user_id_q = await session.execute(
            select(UserBalanceChangeModel.user_id).distinct()
        )
        user_id_list = []
        for u_id in user_id_q:
            user_id = u_id[0]
            if user_id not in nonce_user_id_set:
                user_id_list.append(user_id)
                await session.execute(
                    update(UserBalanceChangeModel)
                    .filter(UserBalanceChangeModel.user_id == user_id)
                    .values(id=-1)
                )
                
        print(user_id_list)
        await session.commit()
