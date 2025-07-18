from fastapi import APIRouter

from app.services import DevicesService

router = APIRouter()

devices_service = DevicesService()


@router.post("/{device_hash}/ping")
async def ping_from_device(device_hash: str):
    await devices_service.ping(device_hash)
    return "ok"
