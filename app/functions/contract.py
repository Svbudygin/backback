from sqlalchemy import select, false
from sqlalchemy.ext.asyncio import AsyncSession

from app import exceptions
from app.core.session import async_session
from app.models.FeeContractModel import FeeContractModel
from app.models.TrafficWeightContractModel import TrafficWeightContractModel
from app.schemas.ContractScheme import *


async def _find_fee_contract_by_id(contract_id: str, session: AsyncSession) -> FeeContractModel:
    contract_req = await session.execute(
        select(FeeContractModel)
        .filter(
            FeeContractModel.id == contract_id))
    
    result = contract_req.scalars().first()
    if result is None:
        raise exceptions.FeeContractNotFoundException()
    return result


async def _find_traffic_weight_contract_by_id(
        contract_id: str, session: AsyncSession) -> TrafficWeightContractModel | None:
    contract_req = await session.execute(
        select(TrafficWeightContractModel)
        .filter(
            TrafficWeightContractModel.id == contract_id))
    result = contract_req.scalars().first()
    if result is None:
        raise exceptions.TrafficWeightContractNotFoundException()
    return result


# -------------------------------------------------CREATE------------------------------------------
async def create_fee_contract(
        contract_scheme_request_create: FeeRequestCreate
) -> FeeResponse:
    async with async_session() as session:
        contract_model: FeeContractModel = FeeContractModel(
            **contract_scheme_request_create.__dict__,
            is_deleted=False
        )
        session.add(contract_model)
        await session.commit()
        await session.refresh(contract_model)
        
        return FeeResponse(
            **contract_model.__dict__
        )


async def create_traffic_weight_contract(
        contract_scheme_request_create: TrafficWeightRequestCreate
) -> TrafficWeightResponse:
    async with async_session() as session:
        contract_model: TrafficWeightContractModel = TrafficWeightContractModel(
            **contract_scheme_request_create.__dict__,
            is_deleted=False
        )
        session.add(contract_model)
        await session.commit()
        
        return TrafficWeightResponse(
            **contract_model.__dict__
        )


# -------------------------------------------------LIST--------------------------------------------
async def list_fee_contract(
        contract_scheme_request_list: RequestList
) -> FeeResponseList:
    async with async_session() as session:
        contract_list = await session.execute(
            select(FeeContractModel).filter(
                FeeContractModel.offset_id < contract_scheme_request_list.last_offset_id)
            .filter(
                FeeContractModel.is_deleted == false())
            .order_by(
                FeeContractModel.offset_id.desc())
            .limit(contract_scheme_request_list.limit))
        return FeeResponseList(items=[i.__dict__ for i in contract_list.scalars().fetchall()])


async def list_traffic_weight_contract(
        contract_scheme_request_list: RequestList
) -> TrafficWeightResponseList:
    async with async_session() as session:
        contract_list = await session.execute(
            select(TrafficWeightContractModel).filter(
                TrafficWeightContractModel.offset_id < contract_scheme_request_list.last_offset_id)
            .filter(
                TrafficWeightContractModel.is_deleted == false())
            .order_by(
                TrafficWeightContractModel.offset_id.desc())
            .limit(contract_scheme_request_list.limit))
        return TrafficWeightResponseList(items=[i.__dict__ for i in contract_list.scalars().fetchall()])


# -------------------------------------------------DELETE-------------------------------------------
async def delete_fee_contract(
        contract_scheme_request_delete: RequestDelete
) -> FeeResponse | None:
    async with async_session() as session:
        contract_model = await _find_fee_contract_by_id(
            contract_scheme_request_delete.id,
            session
        )
        contract_model.is_deleted = True
        await session.commit()
        
        return FeeResponse(
            **contract_model.__dict__
        )


async def delete_traffic_weight_contract(
        contract_scheme_request_delete: RequestDelete
) -> TrafficWeightResponse | None:
    async with async_session() as session:
        contract_model = await _find_traffic_weight_contract_by_id(
            contract_scheme_request_delete.id,
            session
        )
        contract_model.is_deleted = True
        await session.commit()
        
        return TrafficWeightResponse(
            **contract_model.__dict__
        )


# -------------------------------------------------UPDATE-------------------------------------------
async def update_fee_contract(
        contract_scheme_request_update: FeeRequestUpdate
) -> FeeResponse | None:
    async with (async_session() as session):
        contract_model = await _find_fee_contract_by_id(
            contract_scheme_request_update.id,
            session
        )
        
        contract_model.update_if_not_none(
            contract_scheme_request_update.__dict__
        )
        await session.commit()
        
        return FeeResponse(
            **contract_model.__dict__
        )


async def update_traffic_weight_contract(
        contract_scheme_request_update: TrafficWeightRequestUpdate
) -> TrafficWeightResponse | None:
    async with (async_session() as session):
        contract_model = await _find_traffic_weight_contract_by_id(
            contract_scheme_request_update.id,
            session
        )

        contract_model.update_if_not_none(
            contract_scheme_request_update.__dict__
        )
        await session.commit()
        
        return TrafficWeightResponse(
            **contract_model.__dict__
        )

# -------------------------------------------------TEST--------------------------------------------
# CREATE
# print(asyncio.run(create_contract(
#     ContractSchemeRequestCreate(
#         merchant_id="f91caf75-8a2a-401e-8008-842c25184ace",
#         team_id="4676150b-ee35-43e1-a034-4e6d55010d6e",
#         user_id="4676150b-ee35-43e1-a034-4e6d55010d6e",
#         inbound_fee=10000,
#         outbound_fee=0,
#         inbound_traffic_weight=500000,
#         outbound_traffic_weight=0,
#         comment="Test"
# ))))

# LIST
# print(asyncio.run(list_contract(ContractSchemeRequestList(
#     last_offset_id=7,
#     limit=2,
# ))))
# DELETE
# print(asyncio.run(delete_contract(ContractSchemeRequestDelete(
#     id='0baaaee1-c735-4c30-a3ec-4712560dc967'
# ))))
# UPDATE
# print(asyncio.run(update_contract(ContractSchemeRequestUpdate(
#     id="0baaaee1-c735-4c30-a3ec-4712560dc967",
#     merchant_id="f91caf75-8a2a-401e-8008-842c25184ace",
#     team_id="4676150b-ee35-43e1-a034-4e6d55010d6e",
#     user_id=None,
#     inbound_fee=1000000000000,
#     outbound_fee=0,
#     inbound_traffic_weight=500000,
#     outbound_traffic_weight=0,
#     comment="BUR",
# ))))

# TODO create filters like here
# async def update_contract(
#         contract_scheme_request_update: ContractSchemeRequestUpdateDB
# ) -> ContractSchemeRequestCreate:
#     filter_keys = []
#     for key, val in contract_scheme_request_update.__dict__.items():
#         if val is not None:
#             filter_keys.append(key)
#     async with async_session() as session:
#         print(contract_scheme_request_update.__getattribute__('team_id'))
#         contract_req = await session.execute(
#             select(ContractModel)
#             .filter(
#                 ContractModel.team_id == contract_scheme_request_update.team_id)
#             .filter(
#                 *[ContractModel.__getattribute__(ContractModel, i) ==
#                   contract_scheme_request_update.__getattribute__(i)
#                   for i in filter_keys]))
#         contract_model = contract_req.scalars().one()
#         contract_model.is_deleted = True
#         await session.commit()
#
#         return ContractSchemeResponseCreate(
#             **contract_model.__dict__
#         )
