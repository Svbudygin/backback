from fastapi import APIRouter, Depends
from app.schemas.GenericScheme import GenericListResponse
from app.schemas.admin.GeoScheme import (
    GeoScheme
)
from app.schemas.admin.GeoSettingsScheme import (
    UpdateGeoSettings,
    ResponseUpdateGeoSettings
)
from app.repositories.admin import geo_repository
from app.schemas.UserScheme import User, UserSupportScheme
from app.api.deps import v2_get_current_user, v2_get_current_support_user

router = APIRouter()

@router.get("/list")
async def get_list_geo(current_user: User = Depends(v2_get_current_user)) -> GenericListResponse[GeoScheme]:
    geo = await geo_repository.get_all(namespace_id=current_user.namespace.id)
    return GenericListResponse(items=geo)

@router.patch("/set_geo_settings/{geo_id}")
async def set_geo_settings(geo_id: int, request: UpdateGeoSettings, current_user: UserSupportScheme = Depends(v2_get_current_support_user)) -> ResponseUpdateGeoSettings:
    response = await geo_repository.set_geo_settings(geo_id, request)
    return response

@router.get("/get_geo_settings/{geo_id}")
async def get_geo_settings(geo_id: int, current_user: User = Depends(v2_get_current_user)) -> ResponseUpdateGeoSettings:
    response = await geo_repository.get_geo_settings(id=geo_id)
    return response