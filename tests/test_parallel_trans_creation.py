import asyncio
import httpx
import uuid
import random

password = "713c90aca3efe05b0c07e1141c955d2ea7195b0c72c7c49d594324e918a2eb90"
url = "http://127.0.0.1:8000"
token = ""

payload_template = {
    "amount": 2000000000,
    "hook_uri": "string",
    "type": "card",
    "tag_code": "default",
    "bank": "sber",
    "is_vip": False,
    "merchant_payer_id": "stasdadasring",
    "merchant_transaction_id": ""
}

async def authorize():
    global token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{url}/user/access-token",
            params={"password": password},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print("Authorized successfully.", token)
        else:
            print("Authorization failed:", response.status_code, response.text)


async def create_transaction(session: httpx.AsyncClient, i: int, token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = payload_template.copy()
    payload["merchant_transaction_id"] = f"txn_{uuid.uuid4()}"
    payload["is_vip"] = random.choice([True, False])
    payload["merchant_payer_id"] = (
        random.choice(["whitelist1", "whitelist2"]) if payload["is_vip"] else str(uuid.uuid4())
    )

    print(f"[{i}] Payload: {payload}")

    try:
        response = await session.post(
            f"{url}/external-transaction/create-inbound",
            json=payload,
            headers=headers
        )
        print(f"[{i}] Status: {response.status_code}")
        print(f"[{i}] Response: {response.text}")
    except Exception as e:
        print(f"[{i}] Exception: {repr(e)}")


async def parallel_trans_test(n):
    await authorize()
    async with httpx.AsyncClient() as session:
        tasks = [create_transaction(session, i, token) for i in range(n)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(parallel_trans_test(15))

