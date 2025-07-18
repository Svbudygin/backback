from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.file_storage import get_file_by_key
from app.api.deps import v2_get_current_user
from app.schemas.UserScheme import User


router = APIRouter()


@router.get("/{file_key}")
async def get_file(
    file_key: str,
    current_user: User = Depends(v2_get_current_user),
):
    file = await get_file_by_key(file_key)

    return StreamingResponse(
        file["Body"]
    )
