import time
from collections.abc import AsyncGenerator
from typing import List, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
    APIKeyHeader
)
from sqlalchemy.ext.asyncio import AsyncSession

from app import exceptions
from app.core import config, security
from app.core.constants import Role
from app.core.session import async_session
from app.functions.admin.base_services import (
    validate_participants_belong_to_namespace,
)
from app.functions.user import (
    user_get_by_id,
    v2_user_get_by_id,
    v2_user_get_merchant_by_api_secret
)
from app.schemas.UserScheme import (
    AdminUserSchemeResponse,
    ExpandedUserSchemeResponse,
    PaymentSchemeResponse,
    UserSchemeRequestGetById,
    UserSchemeResponse,
    User,
    UserSupportScheme,
    UserTeamScheme,
    UserMerchantScheme,
    WorkingUser,
    get_user_scheme
)
from app.enums import Permission

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="auth/access-token")
token_auth_scheme = APIKeyHeader(name="x-token")
token_auth_scheme_without_auto_error = APIKeyHeader(name="x-token", auto_error=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


auth_scheme = HTTPBearer()
auth_scheme_without_auto_error = HTTPBearer(auto_error=False)


async def get_current_user_(
        bearer: HTTPAuthorizationCredentials = Depends(auth_scheme),
        is_expanded: bool = False,
) -> UserSchemeResponse | ExpandedUserSchemeResponse:
    token = bearer.credentials
    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[security.JWT_ALGORITHM]
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    token_data = security.JWTTokenPayload(**payload)

    if token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, can not use refresh token.",
        )
    now = int(time.time())
    if now < token_data.issued_at or now > token_data.expires_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, token expired or not yet valid.",
        )
    user = await user_get_by_id(UserSchemeRequestGetById(id=token_data.subject))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked."
        )
    if not is_expanded:
        return UserSchemeResponse(**user.__dict__)
    return user


async def get_current_payment(
        bearer: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> PaymentSchemeResponse:
    token = bearer.credentials
    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[security.JWT_ALGORITHM]
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )
    token_data = security.PaymentJWTTokenPayload(**payload)

    if token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, can not use refresh token.",
        )
    now = int(time.time())
    if now < token_data.issued_at or now > token_data.expires_at:
        raise exceptions.PaymentExpiredException()

    return PaymentSchemeResponse(**token_data.__dict__)


async def get_current_user(
        bearer: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> UserSchemeResponse:
    result = await get_current_user_(bearer=bearer, is_expanded=False)
    return result


async def get_current_user_expanded(
        bearer: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> UserSchemeResponse:
    result = await get_current_user_(bearer=bearer, is_expanded=True)
    return result


async def get_support_user(
        current_user: AdminUserSchemeResponse = Depends(get_current_user_expanded),
) -> UserSchemeResponse:
    if current_user.role != Role.SUPPORT:
        raise exceptions.UserWrongRoleException(roles=[Role.SUPPORT])
    return current_user


async def get_support_user_in_namespace_args(
        team_id: str | None = None,
        merchant_id: str | None = None,
        current_user: AdminUserSchemeResponse = Depends(get_support_user),
) -> UserSchemeResponse:
    if team_id is None and merchant_id is None:
        raise HTTPException(status_code=422, detail="Neither team_id or merchant_id should be filled")
    await validate_participants_belong_to_namespace(
        merchant_id=merchant_id, team_id=team_id, namespace=current_user.namespace
    )

    return current_user


async def role_required(role: str, allowed_roles: List[str]):
    if role not in allowed_roles:
        raise HTTPException(status_code=422, detail="Invalid role")
    return role


def permissions_required(
        permissions: List[Permission]
):
    async def permissions_checker(current_user: UserSchemeResponse = Depends(get_current_user)) -> UserSchemeResponse:
        if (
                current_user is not None
                # and current_user.user_role is not None
                # and set(p.value for p in permissions).issubset(set(current_user.user_role.permissions))
                and current_user.access_matrix is not None
                and set(p.value for p in permissions).issubset(set(current_user.access_matrix))
        ):
            return current_user

        raise HTTPException(status_code=403)

    return permissions_checker


# -------------------------------------NEW--------------------------------------------------------

async def v2_get_current_user(bearer: HTTPAuthorizationCredentials = Depends(auth_scheme)) -> User:
    token = bearer.credentials

    try:
        payload = jwt.decode(
            token, config.settings.SECRET_KEY, algorithms=[security.JWT_ALGORITHM]
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials.",
        )

    token_data = security.JWTTokenPayload(**payload)

    if token_data.refresh:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, can not use refresh token.",
        )

    now = int(time.time())

    if now < token_data.issued_at or now > token_data.expires_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, token expired or not yet valid.",
        )

    user = await v2_user_get_by_id(token_data.subject)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked."
        )

    return get_user_scheme(user)


async def v2_get_current_support_user(current_user: User = Depends(v2_get_current_user)) -> UserSupportScheme:
    if current_user.role != Role.SUPPORT:
        raise exceptions.UserWrongRoleException(roles=[Role.SUPPORT])

    return current_user


async def v2_get_current_team_user(current_user: User = Depends(v2_get_current_user)) -> UserTeamScheme:
    if current_user.role != Role.TEAM:
        raise exceptions.UserWrongRoleException(roles=[Role.TEAM])

    return current_user


async def v2_get_current_merchant_user(current_user: User = Depends(v2_get_current_user)) -> UserMerchantScheme:
    if current_user.role != Role.MERCHANT:
        raise exceptions.UserWrongRoleException(roles=[Role.MERCHANT])

    return current_user


async def v2_get_current_working_user(current_user: User = Depends(v2_get_current_user)) -> WorkingUser:
    if current_user.role != Role.MERCHANT and current_user.role != Role.TEAM:
        raise exceptions.UserWrongRoleException(roles=[Role.MERCHANT, Role.TEAM])

    return current_user


def v2_get_current_support_user_with_permissions(
        permissions: List[Permission]
):
    async def permissions_checker(
            current_user: UserSupportScheme = Depends(v2_get_current_support_user)) -> UserSupportScheme:
        if (
                current_user is not None
                and current_user.access_matrix is not None
                and (set(p.value for p in permissions).issubset(set(current_user.access_matrix)))
        ):
            return current_user

        raise HTTPException(status_code=403)

    return permissions_checker


async def get_current_merchant_user_by_x_token(api_secret: str = Depends(token_auth_scheme)):
    return await v2_user_get_merchant_by_api_secret(api_secret)


async def get_current_user_by_x_token_or_bearer(
    api_secret: str = Depends(token_auth_scheme_without_auto_error),
    bearer: HTTPAuthorizationCredentials = Depends(auth_scheme_without_auto_error)
) -> User:
    if bearer:
        return await v2_get_current_user(bearer)

    if api_secret:
        return await v2_user_get_merchant_by_api_secret(api_secret)

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials.",
    )


def get_current_user_any_role(roles: List[str]):
    async def roles_checker(current_user: User = Depends(v2_get_current_user)) -> User:
        if current_user.role in roles:
            return current_user
        
        raise HTTPException(status_code=403)
    
    return roles_checker
