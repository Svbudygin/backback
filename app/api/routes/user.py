import time
from typing import Tuple

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_cache.decorator import cache
from pydantic import ValidationError
from sqlalchemy import select

import app.functions.balance as fb
from app.api.deps import v2_get_current_user, v2_get_current_merchant_user, v2_get_current_working_user
from app.core import config, security
from app.core.constants import (
    CACHE_TIMEOUT_SMALL_S,
    BalanceStatsPeriodName,
    Direction,
    Role
)
from app.core.security import get_password_hash
from app.core.session import async_session, ro_async_session
from app.functions.user import (
    change_switcher,
    v2_user_get_by_id,
    v2_user_get_by_password_hash,
    validate_team_by_api
)
from app.models import CurrencyModel
from app.schemas.BalanceScheme import BalanceStatsResponse
from app.schemas.UserScheme import (
    AuthSchemeAccessTokenResponse,
    AuthSchemeRefreshTokenRequest,
    UserSchemeRequestGetBalances,
    UserSchemeRequestGetByPassword,
    UserSchemeRequestGetByPasswordBody,
    User,
    WorkingUser,
    UserMerchantScheme
)
from app.utils.time import get_period_dates

router = APIRouter()


@router.post("/access-token", response_model=AuthSchemeAccessTokenResponse)
async def login_access_token_route(
        password_scheme1: UserSchemeRequestGetByPassword = Depends(),
        password_scheme2: UserSchemeRequestGetByPasswordBody = None
) -> AuthSchemeAccessTokenResponse:
    domain = password_scheme1.domain
    if password_scheme1.password == None:
        password = password_scheme2.password
    else:
        password = password_scheme1.password
    """Enter password and get access-token"""
    user = await v2_user_get_by_password_hash(get_password_hash(password))

    if domain is None:
        return security.generate_access_token_response(subject=user.id, role=user.role)

    # if user.role in [Role.TEAM, Role.MERCHANT, Role.SUPPORT, Role.AGENT]:
    #     allowed_domains = config.settings.ALLOWED_DOMAINS.get(user.namespace.name, [])
    #     if any(d in domain for d in allowed_domains):
    #         pass
    #     else:
    #         raise exceptions.UserNotFoundException()

    return security.generate_access_token_response(subject=user.id, role=user.role)


@router.post("/refresh-token")
async def refresh_token_route(
        refresh_token_request_scheme: AuthSchemeRefreshTokenRequest,
) -> AuthSchemeAccessTokenResponse:
    """Enter refresh token and get (access-token, refresh-token)"""
    try:
        payload = jwt.decode(
            refresh_token_request_scheme.refresh_token,
            config.settings.SECRET_KEY,
            algorithms=[security.JWT_ALGORITHM],
        )
    except (jwt.DecodeError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, unknown error",
        )
    
    # JWT guarantees payload will be unchanged (and thus valid), no errors here
    token_data = security.JWTTokenPayload(**payload)
    
    if not token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, cannot use access token",
        )
    now = int(time.time())
    if now < token_data.issued_at or now > token_data.expires_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, token expired or not yet valid",
        )
    
    user = await v2_user_get_by_id(token_data.subject)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    
    return security.generate_access_token_response(subject=str(user.id), role=user.role)


@router.get("/me", response_model=User)
async def get_current_user_route(
        current_user: User = Depends(v2_get_current_user),
):
    """Get current user"""
    if 'currency_id' not in current_user:
        return current_user

    async with ro_async_session() as session:
        currency_name_q = await session.execute(
            select(CurrencyModel.name).where(
                CurrencyModel.id == current_user.currency_id
            )
        )
        currency_name = currency_name_q.scalars().first()
        current_user.currency_id = currency_name
    
    return current_user


@router.get("/balances")
@cache(expire=CACHE_TIMEOUT_SMALL_S)
async def get_balances(
        current_user: UserMerchantScheme = Depends(v2_get_current_merchant_user),
):
    balances: Tuple[int, int, int, int, int, int] = await fb.get_balances_transaction(
        user_id=current_user.id
    )
    return UserSchemeRequestGetBalances(
        trust_balance=balances[0],
        locked_balance=balances[1],
        profit_balance=balances[2],
        fiat_trust_balance=balances[3],
        fiat_locked_balance=balances[4],
        fiat_profit_balance=balances[5],
    )


@router.get("/balances/stats")
async def get_balances_stats(
        period_name: BalanceStatsPeriodName,
        current_user: User = Depends(v2_get_current_user),
) -> BalanceStatsResponse:
    date_from, date_to = await get_period_dates(period_name=period_name)
    balances_stats: BalanceStatsResponse = await fb.get_balance_stats(
        user_id=current_user.id,
        balance_id=current_user.balance_id,
        role=current_user.role,
        date_from=date_from,
        date_to=date_to,
        is_agent=current_user.role == Role.AGENT,
    )

    return balances_stats


@router.get("/balances/estimated-fiat-balance")
async def get_balances(
        current_user: UserMerchantScheme = Depends(v2_get_current_merchant_user),
):
    estimated_fiat_balance = await fb.get_estimated_fiat_balance(
        user_id=current_user.id, currency_id=current_user.currency_id
    )
    return estimated_fiat_balance


@router.get("/balances/estimated-fiat-trust-balance")
async def get_balances(
        current_user: UserMerchantScheme = Depends(v2_get_current_merchant_user),
):
    estimated_fiat_balance = await fb.get_estimated_fiat_balance(
        user_id=current_user.id, currency_id=current_user.currency_id
    )
    return {"trust_balance": estimated_fiat_balance}


@router.put("/enable-inbound", response_model=WorkingUser)
async def enable_current_user_route(
        current_user: WorkingUser = Depends(v2_get_current_working_user),
) -> WorkingUser:
    return await change_switcher(
        user_id=current_user.id, value=True, direction=Direction.INBOUND
    )


@router.put("/disable-inbound", response_model=WorkingUser)
async def enable_current_user_route(
        current_user: WorkingUser = Depends(v2_get_current_working_user),
) -> WorkingUser:
    return await change_switcher(
        user_id=current_user.id, value=False, direction=Direction.INBOUND
    )


@router.put("/enable-outbound", response_model=WorkingUser)
async def enable_current_user_route(
        current_user: WorkingUser = Depends(v2_get_current_working_user),
) -> WorkingUser:
    return await change_switcher(
        user_id=current_user.id, value=True, direction=Direction.OUTBOUND
    )


@router.put("/disable-outbound", response_model=WorkingUser)
async def enable_current_user_route(
        current_user: WorkingUser = Depends(v2_get_current_working_user),
) -> WorkingUser:
    return await change_switcher(
        user_id=current_user.id, value=False, direction=Direction.OUTBOUND
    )

@router.get("/validate-team")
async def validate_team(api_secret: str):
    return await validate_team_by_api(api_secret)
