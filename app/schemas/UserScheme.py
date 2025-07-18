from datetime import datetime
from pydantic import ConfigDict, field_validator
from typing import Optional, Union

from app.core.constants import DECIMALS
from app.schemas.BaseScheme import (
    BaseScheme,
    num_factory,
    str_big_factory,
    str_small_factory,
)
from app.models import UserModel, MerchantModel, TeamModel, SupportModel


# -------------------------------------ROOT-------------------------------------------------------
class UserSchemeRequestCreateRoot(BaseScheme):
    name: str = str_small_factory()


class UserSchemeRequestCreateCWorker(BaseScheme):
    name: str = str_small_factory()


class UserSchemeRequestCreateBWorker(BaseScheme):
    name: str = str_small_factory()


class UserSchemeRequestCreateTVWorker(BaseScheme):
    name: str = str_small_factory()


class UserSchemeRequestCreateTCWorker(BaseScheme):
    name: str = str_small_factory()


# -------------------------------------TEAM-------------------------------------------------------


class UserSchemeRequestCreateTeam(BaseScheme):
    wallet_id: str = str_small_factory()
    namespace: str = str_small_factory()
    name: str = str_small_factory()
    telegram_bot_secret: str | None = str_small_factory()
    telegram_verifier_chat_id: str | None = str_small_factory()
    
    economic_model: str = str_small_factory()
    currency_id: str = str_small_factory()
    credit_factor: int = num_factory(0)


class UserSchemeResponseCreateTeam(BaseScheme):
    wallet_id: str = str_small_factory()
    namespace: str = str_small_factory()
    id: str = str_small_factory()
    name: str = str_small_factory()
    password: str = str_small_factory()
    role: str = str_small_factory()
    create_timestamp: datetime
    is_enabled: bool
    is_blocked: bool
    api_secret: str = str_small_factory()
    trust_balance: int = num_factory()
    profit_balance: int = num_factory()


# -------------------------------------MERCHANT----------------------------------------------------
class UserSchemeRequestCreateMerchant(BaseScheme):
    wallet_id: str = str_small_factory()
    namespace: str = str_small_factory()
    name: str = str_small_factory()
    
    economic_model: str = str_small_factory()
    currency_id: str = str_small_factory()
    credit_factor: int = num_factory(-DECIMALS)


class UserSchemeResponseCreateMerchant(BaseScheme):
    wallet_id: str = str_small_factory()
    namespace: str = str_small_factory()
    id: str = str_small_factory()
    name: str = str_small_factory()
    password: str = str_small_factory()
    role: str = str_small_factory()
    create_timestamp: datetime
    is_enabled: bool
    is_blocked: bool
    api_secret: str = str_small_factory()
    trust_balance: int = num_factory()
    profit_balance: int = num_factory()


# -------------------------------------AGENT-------------------------------------------------------
class UserSchemeRequestCreateAgent(BaseScheme):
    wallet_id: str = str_small_factory()
    namespace: str = str_small_factory()
    name: str = str_small_factory()


class UserSchemeRequestCreateSupport(BaseScheme):
    namespace: str = str_small_factory()
    name: str = str_small_factory()


class UserSchemeResponseCreateAgent(BaseScheme):
    wallet_id: str = str_small_factory()
    namespace: str = str_small_factory()
    id: str = str_small_factory()
    name: str = str_small_factory()
    password: str = str_small_factory()
    role: str = str_small_factory()
    create_timestamp: datetime
    is_blocked: bool = num_factory()
    profit_balance: int = num_factory()


class UserSchemeResponseCreateSupport(BaseScheme):
    id: str = str_small_factory()
    namespace: str = str_small_factory()
    name: str = str_small_factory()
    password: str = str_small_factory()
    role: str = str_small_factory()
    create_timestamp: datetime
    is_blocked: bool = num_factory()


# -------------------------------------USER-------------------------------------------------------
class UserSchemeRequestGetById(BaseScheme):
    id: str = str_small_factory()


class UserSchemeRequestGetBalances(BaseScheme):
    trust_balance: int = num_factory()
    locked_balance: int = num_factory()
    profit_balance: int = num_factory()
    fiat_trust_balance: int = num_factory()
    fiat_locked_balance: int = num_factory()
    fiat_profit_balance: int = num_factory()
    
# class AllBalancesScheme(BaseScheme):
#     balance: int = num_factory()
#     estimated_fiat_balance


class UserSchemeRequestGetByPasswordHash(BaseScheme):
    password_hash: str = str_small_factory()


class UserSchemeRequestGetByApiSecret(BaseScheme):
    api_secret: str = str_small_factory()


class UserSchemeRequestGetByPassword(BaseScheme):
    password: str | None = str_small_factory(None)
    domain: str | None = str_small_factory(None)

class UserSchemeRequestGetByPasswordBody(BaseScheme):
    password: str | None = str_small_factory(None)

class RequestCreatePaymentByApiSecret(BaseScheme):
    api_secret: str = str_small_factory()
    merchant_transaction_id: str = str_small_factory()
    hook_uri: str | None = str_big_factory(None)
    payer_id: str = str_small_factory()
    amount: int = num_factory()
    return_url: str | None = str_big_factory(None)
    merchant_website_name: str | None = str_big_factory(None)
    type: str | None = str_small_factory(None)


class PaymentSchemeResponse(BaseScheme):
    user_role: str = str_small_factory()
    merchant_id: str = str_small_factory()
    payer_id: str = str_small_factory()
    merchant_transaction_id: str = str_small_factory()
    hook_uri: str | None = str_big_factory(None)
    amount: int = num_factory()
    currency_id: str = str_small_factory()


class UserRoleScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    permissions: list[str] = []
    
    @field_validator("permissions", mode='before')
    @classmethod
    def serialize_user_role(cls, permissions):
        return [permission.code for permission in permissions]


class UserSchemeResponse(BaseScheme):
    model_config = ConfigDict(from_attributes=True)
    
    credit_factor: int | None = num_factory(None)
    balance_id: str | None = str_small_factory()
    economic_model: str | None = str_small_factory()
    id: str = str_small_factory()
    name: str = str_small_factory()
    role: str = str_small_factory()
    create_timestamp: datetime
    currency_id: str | None = str_small_factory()
    is_enabled: bool | None
    is_blocked: bool
    trust_balance: int | None = num_factory()
    profit_balance: int = num_factory()
    is_inbound_enabled: bool | None = False
    is_outbound_enabled: bool | None = False
    wallet_id: str | None = str_small_factory()
    namespace: str | None = None
    user_role: UserRoleScheme | None = None
    access_matrix: list[str] | None = None

    @field_validator("access_matrix", mode='before')
    @classmethod
    def serialize_access_matrix(cls, access_matrix):
        if access_matrix is not None and not isinstance(access_matrix, list):
            access_matrix_dict = access_matrix.to_dict()
            return [key for key, value in access_matrix_dict.items() if value]
        else:
            return access_matrix


class AdminUserSchemeResponse(UserSchemeResponse):
    types: list | None = None

    class Config:
        from_attributes = True


class ExpandedUserSchemeResponse(UserSchemeResponse):
    telegram_bot_secret: str | None = str_small_factory()
    telegram_verifier_chat_id: str | None = str_small_factory()
    telegram_appeal_chat_id: str | None = str_small_factory(None)


class UserIdNameResponse(BaseScheme):
    id: str = str_small_factory()
    direction: str = str_small_factory()
    name: str | None = str_small_factory(None)
    status: str | None = str_small_factory(None)
    merchant_transaction_id: str | None = str_small_factory(None)
    transaction_id: str = str_small_factory()
    bank_detail_number: str | None = str_small_factory(None)
    bank_detail_bank: str | None = str_small_factory(None)
    bank_detail_name: str | None = str_small_factory(None)
    amount: int = num_factory()
    telegram_appeal_chat_id: str | None = str_small_factory(None)
    telegram_bot_secret: str | None = str_small_factory(None)


# -------------------------------------AUTH--------------------------------------------------------


class AuthSchemeRefreshTokenRequest(BaseScheme):
    refresh_token: str = str_small_factory()


class AuthSchemeAccessTokenResponse(BaseScheme):
    token_type: str = str_small_factory()
    access_token: str = str_big_factory()
    expires_at: int = num_factory()
    issued_at: int = num_factory()
    refresh_token: str = str_big_factory()
    refresh_token_expires_at: int = num_factory()
    refresh_token_issued_at: int = num_factory()
    role: str = str_small_factory()


# -------------------------------------NEW--------------------------------------------------------

class NamespaceScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: int = num_factory()
    name: str = str_small_factory()
    # wallet_id: str = str_small_factory()
    # withdraw_wallet_id: Optional[str] = str_small_factory()
    # telegram_bot_secret: str = str_small_factory()


class GeoScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: int = num_factory()
    name: str = str_small_factory()


class CurrencyScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class UserScheme(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: str = str_small_factory()
    balance_id: Optional[str] = str_small_factory()
    name: str = str_small_factory()
    role: str = str_small_factory()
    create_timestamp: datetime
    is_blocked: bool
    namespace: Optional['NamespaceScheme'] = None
    is_autowithdraw_enabled: Optional[bool] = None

    currency_id: str = "RUB"
    # is_enabled: bool = True
    # trust_balance: int = 0
    # profit_balance: int = 0

    # credit_factor: int = 0
    # is_inbound_enabled: bool = False
    # is_outbound_enabled: bool = True


class UserTeamScheme(UserScheme):
    geo: 'GeoScheme'
    credit_factor: int
    economic_model: str
    # api_secret: str
    is_inbound_enabled: bool
    is_outbound_enabled: bool
    fiat_max_inbound: int
    fiat_min_inbound: int
    fiat_max_outbound: int
    fiat_min_outbound: int
    today_outbound_amount_used: int
    max_today_outbound_amount_used: int
    max_outbound_pending_per_token: int | None = None
    max_inbound_pending_per_token: int | None = None
    priority_inbound: int
    # currency_id: Optional[str] = None


class UserMerchantScheme(UserScheme):
    geo: 'GeoScheme'
    transaction_auto_close_time_s: int
    transaction_outbound_auto_close_time_s: int
    credit_factor: int
    # api_secret: str
    economic_model: str
    is_inbound_enabled: bool
    is_outbound_enabled: bool
    # telegram_verifier_chat_id: Optional[str]
    currency_id: str
    currency: 'CurrencyScheme'
    left_eps_change_amount_allowed: int
    right_eps_change_amount_allowed: int
    min_fiat_amount_in: int
    max_fiat_amount_in: int
    is_whitelist: bool


class UserSupportScheme(UserScheme):
    access_matrix: list[str] | None = None

    @field_validator("access_matrix", mode='before')
    @classmethod
    def create_access_matrix(cls, matrix):
        if matrix is not None and not isinstance(matrix, list):
            access_matrix_dict = matrix.to_dict()
            return [key for key, value in access_matrix_dict.items() if value]
        else:
            return matrix


class UserMerchantWithTypeResponseScheme(UserMerchantScheme):
    types: list | None = None


User = Union[UserScheme, UserMerchantScheme, UserTeamScheme, UserSupportScheme]
UserModelType = Union[UserModel, MerchantModel, TeamModel, SupportModel]
WorkingUser = Union[UserTeamScheme, UserMerchantScheme]


def get_user_scheme(model_instance):
    if isinstance(model_instance, MerchantModel):
        return UserMerchantScheme.model_validate(model_instance)
    elif isinstance(model_instance, TeamModel):
        return UserTeamScheme.model_validate(model_instance)
    elif isinstance(model_instance, SupportModel):
        return UserSupportScheme.model_validate(model_instance)

    return UserScheme.model_validate(model_instance)
