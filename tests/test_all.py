import asyncio
import datetime
import logging
from random import randint

import aiohttp

logger = logging.getLogger('test')
logger.setLevel(level=logging.DEBUG)
c_handler = logging.StreamHandler()
logger.addHandler(c_handler)

logger.setLevel(logging.DEBUG)

MERCHANT_PASSWORD = '0a3d7474b7cc1f4b49bc041d21628f3f126e3647a3f967fb7712ed258b4ef01c'
TEAM_PASSWORD = '6c0ecfe57f34109046788d14d334aa30d2fca8945184b8228af994ee74e444ee'
TEAM_API_SECRET = 'd59a367cbca9071a54a2089d6a9582cf3ba0e724159de98d66af63a50a09f668'

API_URL = 'https://api.fsd.beauty'


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
        'merchant_payer_id': f'client',
        'merchant_transaction_id': f'burenie123'
    }
    
    async with aiohttp.ClientSession() as session:
        q = await session.post(
            f'{API_URL}/external-transaction/create?currency_id={currency_id}&amount={amount}',
            json=json_data,
            headers=headers)
        response = await q.json()
    return response


async def create_transaction(merchant_token: str):
    b_d = await get_bank_detail_inbound(100_000000, 'RUB', merchant_token)
    e_t = await create_inbound_transaction(currency_id=b_d['bank_detail']['currency'],
                                           amount=10_000000 + randint(0, 30) * 1_000_00,
                                           merchant_token=merchant_token,
                                           bank_detail_id=b_d['bank_detail']['id'],
                                           bank_detail_number=b_d['bank_detail']['number'],
                                           team_id=b_d['team_id']
                                           )
    logger.debug(e_t)
    return e_t


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
        arr.append(i['amount'] / 1_000_000)
    logger.debug(arr)
    return arr


async def create_transaction_h2h(
        currency_id: str,
        amount: int,
        merchant_token: str,
):
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {merchant_token}',
    }
    
    json_data = {
        'amount': amount,
        'direction': 'inbound',
        'hook_uri': 'https://merchant.com/callback',
        'currency_id': currency_id,
        'merchant_payer_id': f'client{amount}{datetime.datetime.now()}',
        'merchant_transaction_id': f'burenie123',
        'type': "card"
    }
    
    async with aiohttp.ClientSession() as session:
        q = await session.post(
            f'{API_URL}/external-transaction/create-inbound',
            json=json_data,
            headers=headers)
        response = await q.json()
    return response
    

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


async def accept_from_device(team_api_secret: str, amount: int):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    
    json_data = {
        'api_secret': f'{team_api_secret}',
        'message': {
            'extra_text': f'Зачислено {amount} р',
            'title': '900'
        },
        'device_hash': '',
    }
    
    async with aiohttp.ClientSession() as session:
        response = await session.put(f'{API_URL}/external-transaction/accept-from-device', headers=headers,
                                     json=json_data)
        
        data = await response.json()
        logger.debug(f'{amount} {data}')
        return data


iteration = 0
finish = 0


async def create_and_accept(limit: int, merchant_token: str, team_token: str):
    global iteration
    it = iteration
    iteration += 1
    
    timer = datetime.datetime.now()
    start = timer
    await asyncio.gather(*[create_transaction_h2h('RUB',
                                                  10_000_000 + randint(0, 3000) * 1_000,
                                                  merchant_token) for _ in range(limit)])
    logger.info(f'create {it} {limit} transactions: {datetime.datetime.now() - timer}')

    timer = datetime.datetime.now()
    arr = await list_transactions(team_token, limit=limit)
    logger.info(f'list {it} {limit} transactions: {datetime.datetime.now() - timer}')
    
    # timer = datetime.datetime.now()
    # await asyncio.gather(*[accept_from_device(TEAM_API_SECRET, arr[i]) for i in range(limit)])
    # logger.info(f'accept_from_device {it} {limit} transactions: {datetime.datetime.now() - timer}')
    # logger.info(f'TOTAL {it}: {datetime.datetime.now() - start}')

    global finish
    finish += 1


async def test_all(limit: int):
    merchant_token = await test_auth(MERCHANT_PASSWORD)
    team_token = await test_auth(TEAM_PASSWORD)
    await create_and_accept(limit, merchant_token, team_token)


async def iter_test(limit: int):
    timer = 0
    merchant_token = await test_auth(MERCHANT_PASSWORD)
    team_token = await test_auth(TEAM_PASSWORD)
    
    while True:
        asyncio.ensure_future(create_and_accept(limit, merchant_token, team_token))
        await asyncio.sleep(1)
        timer += 1
        logger.warning(f"TIMER-FINISH {timer - finish} TIMER {timer}")
        break

if __name__ == '__main__':
    asyncio.run(iter_test(5))
    # asyncio.run(iter_test(10))
