from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user
from app.schemas.GenericScheme import GenericListResponseWithTypes
from app.schemas.UserScheme import UserSupportScheme
from app.schemas.admin.TagScheme import TagScheme
from app.repositories.admin import tags_repository

router = APIRouter()


@router.get("/")
async def get_tags(
    current_user: UserSupportScheme = Depends(v2_get_current_support_user)
) -> GenericListResponseWithTypes[TagScheme]:
    tags = await tags_repository.get_all()
    tags_sorted = sorted(tags, key=lambda tag: tag.name != "default")
    return GenericListResponseWithTypes(items=tags_sorted)
