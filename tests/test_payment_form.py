import asyncio
import time

import aiohttp

MERCHANT_API_SECRET = 'kjh322k3245k525252lg1lfslsfgg42'
API_URL = 'https://api.fsd.beauty'
# API_URL = 'http://127.0.0.1:8000'


async def run():
    async with aiohttp.ClientSession() as session:
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
        }
        
        params = {
            'api_secret': MERCHANT_API_SECRET,
            'payer_id': f'uvaraudi{time.time()}',
        }
        response = await session.post(f'{API_URL}/payment-form/payer-access-token',
                                      params=params,
                                      headers=headers)
        r = await response.json()
        print(r)


async def test_all(limit: int):
    await asyncio.gather(*[run() for _ in range(limit)])


if __name__ == '__main__':
    asyncio.run(test_all(40))
