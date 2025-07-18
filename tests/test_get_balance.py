import asyncio
import aiohttp

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3N1ZWRfYXQiOjE3MTA1NzExMzIsImV4cGlyZXNfYXQiOjE3MTEyNjIzMzIsInN1YiI6ImQ2MzM0ODY0LWZiNzMtNDc0OC04ZDMwLTRlMzlhMThkNmNiMyIsInJlZnJlc2giOmZhbHNlfQ.o8pevPgvym8d6pid4_B8vIfgrVIWBbR0QKXOb8cHN_4',
}


async def run():
    async with aiohttp.ClientSession() as session:
        response = await session.get('https://api.fsd.beauty/user/balances', headers=headers)
        ans = await response.json()
        print(ans)


async def test(limit: int):
    await asyncio.gather(*[run() for _ in range(limit)])


if __name__ == '__main__':
    asyncio.run(test(limit=30))
