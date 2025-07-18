import asyncio
import datetime
import json
import time

import requests
import aiohttp


MERCHANT_PASSWORD = '0a3d7474b7cc1f4b49bc041d21628f3f126e3647a3f967fb7712ed258b4ef01c'
TEAM_PASSWORD = '6c0ecfe57f34109046788d14d334aa30d2fca8945184b8228af994ee74e444ee'
TEAM_API_SECRET = 'd59a367cbca9071a54a2089d6a9582cf3ba0e724159de98d66af63a50a09f668'

API_URL = 'https://api.fsd.beauty'
# API_URL = 'https://162.19.204.29:6443'
# API_URL = 'http://127.0.0.1:64864'
# API_URL = 'http://162.19.204.29:443'
# API_URL = 'http://127.0.0.1:8000'
# API_URL = 'http://162.19.204.29:30180'
# API_URL = 'https://api.1spin.io'
# API_URL = 'http://127.0.0.1:59047'


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

def log(data):
    print(json.dumps(data))


async def create(token: str):
    headers = {
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'Authorization': f'Bearer {token}',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': f'{API_URL}',
        'Referer': f'{API_URL}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'accept': 'application/json',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    json_data = {
        'amount': 66000000,
        'direction': 'outbound',
        'bank_detail_id': '3f22900f-a225-435e-b072-9f86d0945fdf',
        'additional_info': None,
        'currency_id': 'RUB',
        'outbound_bank_detail_number': '22022028193840044',
        'status': 'pending',
        'team_id': 'd6334864-fb73-4748-8d30-4e39a18d6cb3',
        'file_uri': None,
        'bank_detail_number': '2202203392849284',
        'hook_uri': None
    }
    async with aiohttp.ClientSession() as session:
        for _ in range(1):
            response = await session.post(f'{API_URL}/external-transaction/create', headers=headers,
                                          json=json_data)
            r = await response.json()
            log(r)


async def list_trx(token: str):
    headers = {
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'Authorization': f'Bearer {token}',
        'Connection': 'keep-alive',
        'Referer': f'{API_URL}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'accept': 'application/json',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    params = {
        'last_offset_id': '1111100000',
        'limit': MAX,
    }
    async with aiohttp.ClientSession() as session:
        response = await session.get(f'{API_URL}/external-transaction/list', params=params, headers=headers)
        data = await response.json()
    arr = []
    # print(data)
    for i in data['items']:
        arr.append(i['id'])
        # print(i['id'])
        # print(i['id'])
    return arr


async def accept(trx_id, token: str):
    headers = {
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'Authorization': f'Bearer {token}',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': f'{API_URL}',
        'Referer': f'{API_URL}',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'accept': 'application/json',
        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    json_data = {
        'transaction_id': f'{trx_id}',
        'status': 'accept',
    }
    async with aiohttp.ClientSession() as session:
        response = await session.put(f'{API_URL}/external-transaction/update', headers=headers,
                                     json=json_data)
        try:
            data = await response.json()
        except Exception as e:
            print(response.text, response, response.status)
        print(data)
        return data


MAX = 1


async def main():
    merchant_token = await test_auth(MERCHANT_PASSWORD)
    team_token = await test_auth(TEAM_PASSWORD)
    
    timer = datetime.datetime.now()
    for i in range(1):
        await asyncio.gather(*[create(merchant_token) for _ in range(MAX)])
    print(datetime.datetime.now() - timer)
    #
    timer = datetime.datetime.now()
    arr = await list_trx(team_token)
    print('ARR', arr)
    print(datetime.datetime.now() - timer)
    
    # timer = datetime.datetime.now()
    # await asyncio.gather(*[accept(arr[i]) for i in range(MAX)])
    # print(datetime.datetime.now() - timer)


if __name__ == '__main__':
    asyncio.run(main())
