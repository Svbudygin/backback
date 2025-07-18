from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_user
from app.schemas.UserScheme import User
from app.services import info


router = APIRouter()


@router.get('/summary')
async def get_summary(current_user: User = Depends(v2_get_current_user)):
    return await info.get_summary(current_user)
