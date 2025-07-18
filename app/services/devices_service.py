from datetime import datetime

from app.core.redis import redis_client_ping


class DevicesService:
    def __init__(self):
        pass

    async def ping(self, device_hash: str):
        await redis_client_ping.set(device_hash, int(datetime.now().timestamp()))
        return "ok"
