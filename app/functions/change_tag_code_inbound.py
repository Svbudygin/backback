import logging
import app.schemas.v2.ExternalTransactionScheme as v2_ETs
from app.core.constants import (
    DECIMALS,
)

logger = logging.getLogger(__name__)

async def change_tag_code_inbound(request: v2_ETs.H2HCreateInbound) -> v2_ETs.H2HCreateInbound:
    if request.merchant_id == "770badf6-69a0-4ca1-905a-66d786d7365d" or request.merchant_id == "0d5edc63-f04d-4dbb-b1b3-55908d736fc4":
        request = await change_inbound_tag_770badf6(request)
    elif request.merchant_id == "d6f67ae2-8a3a-4081-878d-24eafe441c6b":
        request = await change_inbound_tag_d6f67ae2(request)
    elif request.merchant_id == "3cdd12cb-e46f-4b79-ab4a-47b62c52fe35":
        request = await change_inbound_tag_3cdd12cb(request)
    elif request.merchant_id == "8d3ef031-49bd-494f-9b23-4983d7c173e2":
        request = await change_inbound_tag_8d3ef031(request)
    elif request.merchant_id == "390800f2-3d8b-44ac-8cc0-c229bd097131":
        request = await change_inbound_tag_390800f2(request)
    elif request.merchant_id == "1c77e8bc-eec8-40a0-8d7c-750d2a9cf4d9":
        request = await change_inbound_tag_1c77e8bc(request)
    elif request.merchant_id == "f90112a2-c813-47fc-aed0-8d6240b3f016":
        request = await change_inbound_f90112a2(request)
    elif request.merchant_id == "a1f92a3a-e744-41a0-8820-c77d79057102":
        request = await change_inbound_a1f92a3a(request)
    elif request.merchant_id == "169ea63d-1064-4cd9-b868-8e23c70e08c9":
        request = await change_inbound_169ea63d(request)
    elif request.merchant_id == "bcb293b3-5b82-4846-905b-efb1ca3ca14f":
        request = await change_inbound_bcb293b3(request)
    elif request.merchant_id == "a5f08d0b-96cf-4f7c-a84f-05df990a8c41":
        request = await change_inbound_a5f08d0b(request)
    elif request.merchant_id == "2a4248d6-1139-4ff7-835b-7a29b946fa85":
        request = await change_inbound_2a4248d6(request)
    elif request.merchant_id == "ff346afa-af96-48f3-bb9d-33e4abccf8f0":
        request = await change_inbound_tag_ff346afa(request)
    return request


async def change_inbound_tag_770badf6(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request

async def change_inbound_tag_d6f67ae2(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request

async def change_inbound_tag_3cdd12cb(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_tag_8d3ef031(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_tag_390800f2(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_tag_1c77e8bc(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_f90112a2(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_a1f92a3a(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_169ea63d(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_bcb293b3(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_a5f08d0b(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_2a4248d6(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request


async def change_inbound_tag_ff346afa(request):
    if request.amount >= 1000 * DECIMALS and request.amount <= 2000 * DECIMALS:
        request.tag_code = "in_1000_2000"
    if request.amount >= 2001 * DECIMALS and request.amount <= 4000 * DECIMALS:
        request.tag_code = "in_2001_4000"
    if request.amount >= 4001 * DECIMALS and request.amount <= 8000 * DECIMALS:
        request.tag_code = "in_4001_8000"
    if request.amount >= 8001 * DECIMALS:
        request.tag_code = "in_8001_inf"
    return request