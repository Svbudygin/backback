import asyncio

import aiohttp
import logging
from sqlalchemy import select
import hmac
import hashlib
import json

from app import exceptions
from app.core.constants import REPLICATION_LAG_S
from app.core.session import ro_async_session
from app.models import UserModel, MerchantModel
from app.schemas.CallbackSchema import CallbackSchema
from app.schemas.LogsSchema import *

logger = logging.getLogger(__name__)


async def merchant_callback(
        hook_uri: str,
        direction: str,
        merchant_id: str,
        transaction_id: str,
        amount: int,
        status: str,
        merchant_transaction_id: str,
        request_id: str,
        refilled_amount: str | None = None,
        merchant_trust_change: int | None = None,
        currency_id: str | None = None,
        exchange_rate: int | None = None
):
    callback = hook_callback
    if callback is not None:
        #await asyncio.sleep(REPLICATION_LAG_S)
        
        asyncio.ensure_future(callback(
            hook_uri=hook_uri,
            direction=direction,
            transaction_id=transaction_id,
            amount=amount,
            status=status,
            merchant_transaction_id=merchant_transaction_id,
            merchant_id=merchant_id,
            request_id=request_id,
            merchant_trust_change=merchant_trust_change,
            currency_id=currency_id,
            exchange_rate=exchange_rate
        ))


async def hook_callback(
        hook_uri: str,
        direction: str,
        transaction_id: str,
        amount: int,
        status: str,
        merchant_transaction_id: str,
        merchant_id: str,
        request_id: str,
        merchant_trust_change: int | None = None,
        currency_id: str | None = None,
        exchange_rate: int | None = None
):
    async with aiohttp.ClientSession() as session:
        async with ro_async_session() as db_session:
            api_token_q = await db_session.execute(
                select(MerchantModel.api_secret)
                .filter(MerchantModel.id == merchant_id)
            )
            api_token = api_token_q.scalars().first()
            print('Callback', transaction_id, merchant_transaction_id, {
                "id": transaction_id,
                "status": status,
                "amount": amount,
                "merchant_transaction_id": merchant_transaction_id,
                "merchant_trust_change": merchant_trust_change,
                "currency_id": currency_id,
                "exchange_rate": exchange_rate
            })
            log_data = CallbackTransactionStatLogSchema(
                request_id=request_id,
                merchant_id=merchant_id,
                direction=direction,
                transaction_id=transaction_id,
                status=status,
                amount=amount,
                merchant_transaction_id=merchant_transaction_id,
                merchant_trust_change=merchant_trust_change,
                currency_id=currency_id,
                exchange_rate=exchange_rate
            )

            logger.info(log_data.model_dump_json())
            logger.info(f"[CallbackTransactionStat] - merchant_id = {merchant_id}, direction = {direction}, transaction_id = {transaction_id}, status = {status}, amount = {amount}, merchant_transaction_id = {merchant_transaction_id}, merchant_trust_change = {merchant_trust_change}, currency_id = {currency_id}, exchange_rate = {exchange_rate}")
            if api_token is None:
                raise exceptions.UserNotFoundException()
            try:
                json_data = {
                    "id": transaction_id,
                    "status": status,
                    "amount": amount,
                    "merchant_transaction_id": merchant_transaction_id,
                    "merchant_trust_change": merchant_trust_change,
                    "currency_id": currency_id,
                    "exchange_rate": exchange_rate
                }
                json_string = json.dumps(json_data, separators=(',', ':'), sort_keys=True)
                json_bytes = json_string.encode('utf-8')
                sign = hmac.new(api_token.encode(), json_bytes, digestmod=hashlib.sha512).hexdigest()
                headers = {}
                if merchant_id == "68146490-a9c0-48de-9a0c-2a38fa39b139":
                    headers["Authorization"] = api_token
                else:
                    headers["Signature"] = sign
                request = await session.post(
                    url=hook_uri,
                    json=json_data,
                    headers=headers
                )
                #print('Callback',
                #      transaction_id, merchant_transaction_id, hook_uri, request.status, (await request.json()))
                log_data = CallbackResponseWithTransactionLogSchema(
                    request_id=request_id,
                    transaction_id=transaction_id,
                    merchant_transaction_id=merchant_transaction_id,
                    hook_uri=hook_uri,
                    status=request.status,
                    response=await request.text()
                )

                logger.info(log_data.model_dump_json())
                logger.info(f"""[CALLBACK] - transaction_id = {transaction_id}, merchant_transaction_id = {merchant_transaction_id}, hook_uri = {hook_uri}, status = {request.status}, response = {await request.text()}""")
                return request.status
            except Exception as err:
                #print('Callback error test',
                #      transaction_id,
                #      merchant_transaction_id,
                #      request.status,
                #      err)
                log_data = CallbackErrorWithTransactionLogSchema(
                    request_id=request_id,
                    transaction_id=transaction_id,
                    merchant_transaction_id=merchant_transaction_id,
                    hook_uri=hook_uri,
                    error=str(err)
                )

                logger.info(log_data.model_dump_json())
                logger.info(
                    f"""[CallbackError] - transaction_id = {transaction_id}, merchant_transaction_id = {merchant_transaction_id}, hook_uri = {hook_uri}, error = {err}"""
                )


async def send_callback(
        endpoint_url: str,
        merchant_id: str,
        request_id: str,
        data: CallbackSchema
):
    try:
        async with aiohttp.ClientSession() as client_session:
            async with ro_async_session() as db_session:
                api_token = (await db_session.execute(
                    select(MerchantModel.api_secret)
                    .where(MerchantModel.id == merchant_id)
                )).scalar_one_or_none()

                if api_token is None:
                    raise exceptions.UserNotFoundException()

                log_data = AppealCallbackSendLogSchema(
                    request_id=request_id,
                    merchant_id=merchant_id,
                    endpoint_url=endpoint_url,
                    callback_name=data.name,
                    data=data.model_dump(exclude=["name"])
                )

                logger.info(log_data.model_dump_json())

                logger.info(f"[CallbackSend] - {data.name}. merchant_id = {merchant_id}, endpoint_url = {endpoint_url}, merchant_id = {merchant_id}, data = {data.model_dump(exclude=['name'])}")

                data_json = data.model_dump(exclude=['name'])
                json_string = json.dumps(data_json, separators=(',', ':'), sort_keys=True)
                json_bytes = json_string.encode('utf-8')
                sign = hmac.new(api_token.encode(), json_bytes, digestmod=hashlib.sha512).hexdigest()

                headers = {"Signature": sign}

                request = await client_session.post(
                    url=endpoint_url,
                    json=data_json,
                    headers=headers
                )

                log_data = AppealCallbackResponseLogSchema(
                    request_id=request_id,
                    merchant_id=merchant_id,
                    endpoint_url=endpoint_url,
                    status=request.status,
                    response=await request.text(),
                    callback_name=data.name
                )

                logger.info(log_data.model_dump_json())
                logger.info(f"[CallbackResponse] - {data.name}. merchant_id = {merchant_id}, endpoint_url = {endpoint_url}, status = {request.status}, response = {await request.text()}")
    except Exception as e:
        log_data = AppealCallbackErrorLogSchema(
            request_id=request_id,
            merchant_id=merchant_id,
            endpoint_url=endpoint_url,
            error=str(e),
            callback_name=data.name
        )

        logger.error(log_data.model_dump_json())
        logger.error(f"[CallbackError] - {data.name}. merchant_id={merchant_id}, endpoint_url={endpoint_url}, merchant_id={merchant_id}, error={e}")


if __name__ == '__main__':
    asyncio.run(merchant_callback(
        transaction_id="fcb1053e-3cce-4f8e-8f76-4c21c19f0d04",
        amount=5068000000,
        direction="inbound",
        hook_uri="https://google.com",
        status='close',
        merchant_transaction_id='27120778-a370-4431-bee6-ba87bbfc0066',
        merchant_id='0d5edc63-f04d-4dbb-b1b3-55908d736fc4',
        exchange_rate=92720000
    ))
