import asyncio
import aiohttp

API_URL = 'http://127.0.0.1:8000'

# токен мерчанта
MERCHANT_PASSWORD = '0a3d7474b7cc1f4b49bc041d21628f3f126e3647a3f967fb7712ed258b4ef01c'


# авторизация
async def test_auth(password: str):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
    }
    params = {
        'password': password  # str, ваш токен,
    }
    async with aiohttp.ClientSession() as session:
        q = await session.post(f'{API_URL}/user/access-token', params=params, headers=headers)
        response = await q.json()
    return response['access_token']


# получение реквизитов
async def get_bank_detail_inbound(merchant_token: str) -> dict:
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {merchant_token}',
    }
    
    params = {
        'currency_id': 'RUB',  # str, "RUB"
        'amount': '101_000_000',  # int, настоящие значение * 1_000_000
        'type': 'card'  # str, "card", "phone"
    }
    async with aiohttp.ClientSession() as session:
        q = await session.get(
            f'{API_URL}/external-transaction/inbound-bank-detail',
            params=params,
            headers=headers)
        try:
            response = await q.json()
        except Exception as e:
            print(q.status)
            print(e)
    return response


async def create_transaction(merchant_token: str) -> dict:
    async with aiohttp.ClientSession() as session:
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {merchant_token}',
        }
        
        params = {
            'amount': 105_000000,  # int, настоящие значение * 1_000_000
            'direction': 'inbound',  # "inbound", если pay in, иначе "outbound"
            
            # str, ["bank_detail"]["id"] из ответа на запрос inbound-bank-detail
            'bank_detail_id': 'c3df101a-23e8-45a2-a905-d1184d9c2f00',
            
            # str, ["bank_detail"]["number"] из ответа на запрос inbound-bank-detail
            "bank_detail_number": "2200284937449487",
            
            # str, ["team_id"] из ответа на запрос inbound-bank-detail
            "team_id": "d6334864-fb73-4748-8d30-4e39a18d6cb3",
            
            #
            "hook_uri": "http://sfdj",
            
            # str, можно null
            "additional_info": "string",
            
            # str, ["currency_id"] из ответа на запрос inbound-bank-detail
            "currency_id": "RUB",
            
            # str, это ваш id транзакции
            "merchant_transaction_id": "merchantid123",
            
            # str, это id вашего плтательщика. Нужно для антифрода.
            "merchant_payer_id": "payerid1234"
        }
        
        q = await session.post(f'{API_URL}/external-transaction/create',
                               json=params, headers=headers)
        print(q.status)
        response = await q.json()
        return response


async def get_transaction(merchant_token: str) -> dict:
    async with aiohttp.ClientSession() as session:
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {merchant_token}',
        }
        
        params = {
            'merchant_transaction_id': f'merchantid123'  # str, значение вашей транзакции,
        }
        
        q = await session.get(f'{API_URL}/external-transaction/get',
                              params=params, headers=headers)
        response = await q.json()
        return response


async def test():
    token = await test_auth(password=MERCHANT_PASSWORD)
    print(token)
    
    card = await get_bank_detail_inbound(token)
    print(card)
    
    transaction = await create_transaction(token)
    print(transaction)
    
    transaction_info = await get_transaction(token)
    print(transaction_info)


if __name__ == '__main__':
    asyncio.run(test())
