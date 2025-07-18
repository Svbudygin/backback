import asyncio
import datetime
import json
import time
from random import randint

import requests
import aiohttp


def log(data):
    print(json.dumps(data))


async def create():
    headers = {
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZWRfYXQiOjE3MDk4MTE2OTAsImV4cGlyZXNfYXQiOjE3MTA1MDI4OTAsInN1YiI6IjBkNWVkYzYzLWYwNGQtNGRiYi1iMWIzLTU1OTA4ZDczNmZjNCIsInJlZnJlc2giOmZhbHNlfQ.kapcANBFOvqrYXqgBU0cB-rI1Q1dm63gBnJYGbCV_Ls',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'http://127.0.0.1:8000',
        'Referer': 'http://127.0.0.1:8000/',
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
        'amount': 4900000000 + randint(0, 10000) % 10000 * 1000000,
        'direction': 'inbound',
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
            response = await session.post('http://127.0.0.1:8000/external-transaction/create', headers=headers,
                                          json=json_data)
            r = await response.json()
            log(r)


async def list_trx():
    headers = {
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZWRfYXQiOjE3MDk4MTE3NTgsImV4cGlyZXNfYXQiOjE3MTA1MDI5NTgsInN1YiI6ImQ2MzM0ODY0LWZiNzMtNDc0OC04ZDMwLTRlMzlhMThkNmNiMyIsInJlZnJlc2giOmZhbHNlfQ.NsI4AnxpjNUQs9qnkIeILFhuH_VCCUPvWYRsbcBkkOM',
        'Connection': 'keep-alive',
        'Referer': 'http://127.0.0.1:8000/',
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
        response = await session.get('http://127.0.0.1:8000/external-transaction/list', params=params, headers=headers)
        data = await response.json()
    arr = []
    # print(data)
    for i in data['items']:
        arr.append(i['id'])
        # print(i['id'])
        # print(i['id'])
    return arr


async def accept(trx_id):
    headers = {
        'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZWRfYXQiOjE3MDk4MTE3NTgsImV4cGlyZXNfYXQiOjE3MTA1MDI5NTgsInN1YiI6ImQ2MzM0ODY0LWZiNzMtNDc0OC04ZDMwLTRlMzlhMThkNmNiMyIsInJlZnJlc2giOmZhbHNlfQ.NsI4AnxpjNUQs9qnkIeILFhuH_VCCUPvWYRsbcBkkOM',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        'Origin': 'http://127.0.0.1:8000',
        'Referer': 'http://127.0.0.1:8000/',
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
        response = await session.put('http://127.0.0.1:8000/external-transaction/update', headers=headers,
                                     json=json_data)
        try:
            data = await response.json()
        except Exception as e:
            print(response.text, response, response.status)
        print(data)
        return data


MAX = 200


async def main():
    timer = datetime.datetime.now()
    for i in range(1):
        await asyncio.gather(*[create() for _ in range(MAX)])
    print(datetime.datetime.now() - timer)

    timer = datetime.datetime.now()
    arr = await list_trx()
    print('ARR', arr)
    print(datetime.datetime.now() - timer)

    timer = datetime.datetime.now()
    await asyncio.gather(*[accept(arr[i]) for i in range(MAX)])
    print(datetime.datetime.now() - timer)


if __name__ == '__main__':
    asyncio.run(main())
