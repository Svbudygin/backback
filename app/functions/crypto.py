import aiohttp
import app.exceptions as exceptions


async def get_amount_by_hash(
        hash: str
) -> int:
    async with aiohttp.ClientSession() as session:
        url = f"https://apilist.tronscanapi.com/api/transaction-info?hash={hash}"
        response = await session.get(url)
        data = await response.json()
        try:
            trc20_info = data["trc20TransferInfo"]
            amount = int(trc20_info[0]["amount_str"])
        except:
            raise exceptions.WrongHashException()
        return amount