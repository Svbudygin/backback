import asyncio
from datetime import datetime

from sqlalchemy import text

from app.core.constants import DECIMALS
from app.core.session import async_session
from app.functions.balance import add_balance_changes

TRANSACTION_ID = 'clearing'


async def clearing_fiat_crypto_profit_daily(
        exchange_rate: int,
        merchant_id: str,
        date_from: datetime = datetime(1970, 1, 1),
        date_to: datetime = datetime.now(),
):
    async with async_session() as session:
        debt_q = await session.execute(text(
            f"""
            SELECT u.id,
                   cast(sum(c.fiat_trust_balance) as BIGINT)
            FROM user_balance_change_model c
            INNER JOIN user_model u ON u.id = c.user_id
            INNER JOIN traffic_weight_contact_model t ON u.id = t.team_id
            WHERE t.merchant_id = '{merchant_id}'
            AND c.create_timestamp >= '{date_from}'
            AND c.create_timestamp < '{date_to}'
            AND merchant_id = '{merchant_id}'
            GROUP BY u.id
                """
        ))
        changes=[]
        for user_id, fiat in debt_q.fetchall():
            print(user_id, fiat, -fiat * DECIMALS // exchange_rate)
            changes.append({
                'transaction_id': TRANSACTION_ID,
                'user_id': user_id,
                'fiat_trust_balance': -fiat,
                'trust_balance': fiat * DECIMALS // exchange_rate,
                'create_timestamp': date_from
            })
        print()
        merchant_debt_q = await session.execute(
            text(f"""
            SELECT u.id,
                   cast(sum(c.fiat_trust_balance) as BIGINT)
            FROM user_balance_change_model c
            INNER JOIN user_model u ON u.id = c.user_id
            WHERE u.id = '{merchant_id}'
            AND c.create_timestamp >= '{date_from}'
            AND c.create_timestamp < '{date_to}'
            GROUP BY u.id""")
        )
        for user_id, fiat  in merchant_debt_q.fetchall():
            print(user_id, fiat, -fiat * DECIMALS // exchange_rate)
            changes.append({
                'transaction_id': TRANSACTION_ID,
                'user_id': user_id,
                'fiat_trust_balance': -fiat,
                'trust_balance': fiat * DECIMALS // exchange_rate,
                'create_timestamp': date_from
            })
        print(changes)
        # await add_balance_changes(session=session,
        #                           changes=changes)
        return {}


if __name__ == '__main__':
    print(asyncio.run(clearing_fiat_crypto_profit_daily(
        exchange_rate=96400000,
        date_from=datetime.strptime('2024-05-01 00:00:00', '%Y-%m-%d %H:%M:%S'),
        date_to=datetime.strptime('2024-05-06 07:00:00', '%Y-%m-%d %H:%M:%S'),
        merchant_id='a5a25687-ab15-4b98-bc37-dc0a1107f888'
    )))
