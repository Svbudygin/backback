import asyncio
import datetime
import logging
from random import randint
import aiohttp
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from app.core import config

logger = logging.getLogger('test')
logger.setLevel(level=logging.DEBUG)
c_handler = logging.StreamHandler()
logger.addHandler(c_handler)
logger.setLevel(logging.DEBUG)

API_URL = 'https://api.fsd.beauty'
MERCHANT_PASSWORD = '0a3d7474b7cc1f4b49bc041d21628f3f126e3647a3f967fb7712ed258b4ef01c'
TEAM_PASSWORD = '6c0ecfe57f34109046788d14d334aa30d2fca8945184b8228af994ee74e444ee'


# авторизация
async def test_auth(password: str):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
    }
    params = {
        'password': password,
    }
    async with aiohttp.ClientSession() as session:
        q = await session.post(f'{API_URL}/user/access-token', params=params, headers=headers)
        response = await q.json()
    return response['access_token']


# получение реквизитов
async def get_bank_detail_inbound(amount: int, currency_id: str, merchant_token: str) -> dict:
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {merchant_token}',
    }
    
    params = {
        'currency_id': 'RUB',
        'amount': '1000',
        'type': 'card'
    }
    async with aiohttp.ClientSession() as session:
        q = await session.get(
            f'{API_URL}/external-transaction/inbound-bank-detail?currency_id={currency_id}&amount={amount}',
            params=params,
            headers=headers)
        try:
            response = await q.json()
        except Exception as e:
            print(q.status)
            print(e)
    return response


# создание pay-in транзакции по известным реквизитам
async def create_inbound_transaction(
        currency_id: str,
        amount: int,
        merchant_token: str,
        bank_detail_id: str,
        bank_detail_number: str,
        team_id: str,
) -> dict:
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {merchant_token}',
    }
    
    json_data = {
        'amount': amount,
        'direction': 'inbound',
        'bank_detail_id': bank_detail_id,
        'bank_detail_number': bank_detail_number,
        'team_id': team_id,
        'hook_uri': 'https://merchant.com/callback',
        'additional_info': '',
        'currency_id': currency_id,
    }
    
    async with aiohttp.ClientSession() as session:
        q = await session.post(
            f'{API_URL}/external-transaction/create?currency_id={currency_id}&amount={amount}',
            json=json_data,
            headers=headers)
        response = await q.json()
    return response


# создание pay-in транзакции вместе с подбором реквизитов
async def create_transaction(merchant_token: str):
    amount = 100_000000 + randint(0, 10000) * 1_000
    b_d = await get_bank_detail_inbound(amount, 'RUB', merchant_token)
    e_t = await create_inbound_transaction(currency_id=b_d['bank_detail']['currency'],
                                           amount=amount,
                                           merchant_token=merchant_token,
                                           bank_detail_id=b_d['bank_detail']['id'],
                                           bank_detail_number=b_d['bank_detail']['number'],
                                           team_id=b_d['team_id']
                                           )
    logger.debug(e_t)
    return e_t


# список всех транзакций
async def list_transactions(team_token: str, limit: int):
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {team_token}',
    }
    
    params = {
        'last_offset_id': 1000000000000000,
        'limit': limit,
    }
    async with aiohttp.ClientSession() as session:
        response = await session.get(f'{API_URL}/external-transaction/list', params=params, headers=headers)
        data = await response.json()
    arr = []
    for i in data['items']:
        arr.append(i['id'])
    logger.debug(arr)
    return arr


# подтвердить транзакции по id
async def accept_by_id(team_token: str, transaction_id: str):
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {team_token}',
    }
    
    json_data = {
        'transaction_id': f'{transaction_id}',
        'status': 'accept',
    }
    async with aiohttp.ClientSession() as session:
        response = await session.put(f'{API_URL}/external-transaction/update',
                                     headers=headers,
                                     json=json_data)
        data = await response.json()
        return data


# создание и подтверждение транзакции
async def simple_test():
    #print(config.settings.CACHE_DB)
    redis = aioredis.from_url(
        url=f'rediss://{config.settings.CACHE_USER}:'
            f'{config.settings.CACHE_PASSWORD}@'
            f'{config.settings.CACHE_HOST}:'
            f'{config.settings.CACHE_PORT}'
    )
    await redis.set('test1', '111111111111')
    # FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    # auth
    # merchant_token = await test_auth(MERCHANT_PASSWORD)
    # team_token = await test_auth(TEAM_PASSWORD)
    #
    # # create transaction
    # await create_transaction(merchant_token)
    #
    # # list transactions
    # arr = await list_transactions(team_token, limit=1)
    #
    # # accept transaction
    # await accept_by_id(team_token, arr[0])


if __name__ == '__main__':
    asyncio.run(simple_test())
