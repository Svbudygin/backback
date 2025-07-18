from typing import List

from fastapi import APIRouter, Depends

from app.api.deps import v2_get_current_support_user_with_permissions
from app.enums import Permission
from app.repositories.admin.traffic_weight_repo import TrafficWeightRepo
from app.schemas.admin.TrafficWeightScheme import TrafficWeightScheme
from app.schemas.GenericScheme import GenericListResponseWithTypes, GenericMerchStatisticRespone
from app.utils.time import get_traffic_period_dates
from app.core.constants import TrafficStatsPeriodName

router = APIRouter()


@router.get("/")
async def list(
    merchant_id: str,
    type: str,
    period_name: TrafficStatsPeriodName,
    bank: str | None = None,
    payment_system: str | None = None,
    is_vip: str | None = None,
    current_user=Depends(
        v2_get_current_support_user_with_permissions([Permission.VIEW_TRAFFIC])
    )
) -> GenericListResponseWithTypes[TrafficWeightScheme]:
    date_from = await get_traffic_period_dates(period_name=period_name)

    traffic_weights: [List[str], List[TrafficWeightScheme]] = await TrafficWeightRepo.list(
        merchant_id=merchant_id,
        type=type,
        date_from=date_from,
        bank=bank,
        payment_system=payment_system,
        is_vip=is_vip
    )

    return GenericListResponseWithTypes(types=traffic_weights[0], items=traffic_weights[1])


@router.get("/merchant_stats")
async def merch_stats(
    merchant_id: str,
    type: str,
    period_name: TrafficStatsPeriodName,
    bank: str | None = None,
    payment_system: str | None = None,
    is_vip: str | None = None,
    current_user=Depends(
        v2_get_current_support_user_with_permissions([Permission.VIEW_TRAFFIC])
    )
) -> GenericMerchStatisticRespone:
    date_from = await get_traffic_period_dates(period_name=period_name)
    merchant_stats = await TrafficWeightRepo.merchant_stats(
        merchant_id=merchant_id,
        type=type,
        date_from=date_from,
        bank=bank,
        payment_system=payment_system,
        is_vip=is_vip
    )
    return GenericMerchStatisticRespone(**merchant_stats)


@router.post("/", response_model=TrafficWeightScheme)
async def create(
    request: TrafficWeightScheme,
    current_user=Depends(
       v2_get_current_support_user_with_permissions([Permission.VIEW_TRAFFIC])
    )
) -> TrafficWeightScheme:
    traffic_weight: TrafficWeightScheme = await TrafficWeightRepo.create(
        **request.model_dump(exclude_none=True),
    )
    return traffic_weight


@router.put("/{id}", response_model=TrafficWeightScheme)
async def update(
    id: str,
    request: TrafficWeightScheme,
    current_user=Depends(
        v2_get_current_support_user_with_permissions([Permission.VIEW_TRAFFIC])
    )
) -> TrafficWeightScheme:
    data = {
        field: getattr(request, field)
        for field in request.__fields_set__
    }

    traffic_weight: TrafficWeightScheme = await TrafficWeightRepo.update(
        id=id, **data
    )
    return traffic_weight


@router.delete("/{id}")
async def delete(
    id: str,
    current_user=Depends(
        v2_get_current_support_user_with_permissions([Permission.VIEW_TRAFFIC])
    )
) -> TrafficWeightScheme:
    traffic_weight: TrafficWeightScheme = await TrafficWeightRepo.delete(id=id)
    return traffic_weight
