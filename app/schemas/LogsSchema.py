from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, computed_field
import json

class BasicLogSchema(BaseModel):
    request_id: Optional[UUID] = Field(None, description='Request ID')
    user_id: Optional[str] = Field(None, description='User ID')
    user_name: Optional[str] = Field(None, description='User name')
    utc_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description='UTC timestamp')


class AllTeamsDisabledLogSchema(BasicLogSchema):
    log_name: str = Field(default="AllTeamsDisabledException", exclude=False)
    payer_id: str
    merchant_id: str
    amount: int
    type: Optional[str] = None
    bank: Optional[str] = None
    banks: Optional[List[str]] = None
    types: Optional[List[str]] = None
    payment_systems: Optional[List[str]] = None
    is_vip: bool
    is_whitelist: bool
    merchant_transaction_id: str

    def model_post_init(self, __context) -> None:
        if self.merchant_id is not None:
            object.__setattr__(self, "user_id", self.merchant_id)


class GetBankDetailLogSchema(BasicLogSchema):
    log_name: str = Field(default="GetBankDetail", exclude=False)

    merchant_transaction_id: str
    amount: int
    type: Optional[str] = None
    merchant_id: str
    payer_id: str
    new_amount: int
    is_vip: bool
    is_whitelist: bool
    bank: Optional[str] = None
    banks: Optional[List[str]] = None
    types: Optional[List[str]] = None
    payment_systems: Optional[List[str]] = None
    final: bool

    def model_post_init(self, __context) -> None:
        if self.merchant_id is not None:
            object.__setattr__(self, "user_id", self.merchant_id)


class UnbindOutboundTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="UnbindOutboundTransaction", exclude=False)

    team_name: str
    team_id: str
    transaction_id: str

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)


class DeleteTransferAssociationTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="DeleteTransferAssociationTransaction", exclude=False)

    team_name: str
    team_id: str
    transaction_id: str

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)


class TransferOutboundTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="TransferOutboundTransaction", exclude=False)

    team_name: str
    team_id: str
    transaction_id: str

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)



class CancelOutboundWithReasonLogSchema(BasicLogSchema):
    log_name: str = Field(default="CancelOutboundWithReason", exclude=False)

    team_name: str
    team_id: str
    transaction_id: str
    reason: str

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)


class UpdatePayOutTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="UpdatePayOutTransaction", exclude=False)

    team_name: str
    team_id: str
    transaction_id: str
    status: str

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)


class BlockedDetailLogSchema(BasicLogSchema):
    log_name: str = Field(default="BlockedDetail", exclude=False)

    id: str
    number: str
    team_id: str
    bank: str
    device_hash: str

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)


class ParseMessageLogSchema(BasicLogSchema):
    log_name: str = Field(default="PARSE MESSAGE", exclude=False)

    api_secret: str
    request: Dict[str, Any]
    parsed_amount: Optional[int]
    parsed_new_amount: Optional[int]
    parsed_bank: Optional[str]
    parsed_digits: Optional[str]
    title: Optional[str]


class SuccessUpdateFromDeviceLogSchema(BasicLogSchema):
    log_name: str = Field(default="SuccessUpdateFromDevice", exclude=False)

    team_id: str
    transaction_id: str

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)


class HoldOutboundTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="HoldOutboundTransaction", exclude=False)

    team_name: str
    team_id: str
    transaction_id: str
    count_hold: int

    def model_post_init(self, __context) -> None:
        if self.team_id is not None:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)


class GetOutboundTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="GetOutboundTransaction", exclude=False)

    team_name: str
    team_id: str
    transaction_id: str

    def model_post_init(self, __context) -> None:
        if self.team_id:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)


class UpdateDetailLogSchema(BasicLogSchema):
    log_name: str = Field(default="UpdateDetail", exclude=False)

    team_name: str
    team_id: str
    id: str
    was_is_vip: bool
    new_is_vip: Optional[bool]
    was_is_active: bool
    new_is_active: Optional[bool]
    fields_was: Dict[str, Any]
    fields_new: Dict[str, Any]

    def model_post_init(self, __context) -> None:
        if self.team_id:
            object.__setattr__(self, "user_id", self.team_id)
            object.__setattr__(self, "user_name", self.team_name)


class CallbackTransactionStatLogSchema(BasicLogSchema):
    log_name: str = Field(default="CallbackTransactionStat", exclude=False)

    merchant_id: str
    direction: str
    transaction_id: str
    status: str
    amount: int
    merchant_transaction_id: str
    merchant_trust_change: Optional[int]
    currency_id: str
    exchange_rate: int

    def model_post_init(self, __context) -> None:
        if self.merchant_id:
            object.__setattr__(self, "user_id", self.merchant_id)



class CreateAppealLogSchema(BasicLogSchema):
    log_name: str = Field(default="CreateAppeal", exclude=False)

    appeal_id: str
    amount: Optional[int] = None
    transaction_id: str
    appeal_team_id: str


class AcceptAppealByTeamNeedSupportConfirmationLogSchema(BasicLogSchema):
    log_name: str = Field(default="AcceptAppealByTeamNeedSupportConfirmation", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str
    appeal_amount: int


class AcceptAppealByRoleLogSchema(BasicLogSchema):
    log_name: str = Field(default="AcceptAppealBy<ROLE>", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str
    appeal_amount: int


class CancelAppealByTeamNeedSupportConfirmationLogSchema(BasicLogSchema):
    log_name: str = Field(default="CancelAppealByTeamNeedSupportConfirmation", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str
    reject_reason: str


class CancelAppealBySupportLogSchema(BasicLogSchema):
    log_name: str = Field(default="CancelAppealBySupport", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str
    reject_reason: str


class AppealUploadTeamStatementByRoleLogSchema(BasicLogSchema):
    log_name: str = Field(default="AppealUploadTeamStatementBy<ROLE>", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str


class AppealUploadMerchantStatementByRoleLogSchema(BasicLogSchema):
    log_name: str = Field(default="AppealUploadMerchantStatementBy<ROLE>", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str


class AppealRequestTeamStatementByRoleLogSchema(BasicLogSchema):
    log_name: str = Field(default="AppealRequestTeamStatementBy<ROLE>", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str


class AppealRequestMerchantStatementByRoleLogSchema(BasicLogSchema):
    log_name: str = Field(default="AppealRequestMerchantStatementBy<ROLE>", exclude=False)

    appeal_id: str
    transaction_id: str
    appeal_team_id: str


class AppealCallbackSendLogSchema(BasicLogSchema):
    log_name: str = Field(default="CallbackSend", exclude=False)

    merchant_id: str
    endpoint_url: str
    callback_name: str
    data: Dict[str, Any]

    def model_post_init(self, __context) -> None:
        if self.merchant_id:
            object.__setattr__(self, "user_id", self.merchant_id)


class AppealCallbackResponseLogSchema(BasicLogSchema):
    log_name: str = Field(default="CallbackResponse", exclude=False)

    merchant_id: str
    endpoint_url: str
    status: int
    response: str
    callback_name: str

    def model_post_init(self, __context) -> None:
        if self.merchant_id:
            object.__setattr__(self, "user_id", self.merchant_id)


class AppealCallbackErrorLogSchema(BasicLogSchema):
    log_name: str = Field(default="CallbackError", exclude=False)

    merchant_id: str
    endpoint_url: str
    error: str
    callback_name: str

    def model_post_init(self, __context) -> None:
        if self.merchant_id:
            object.__setattr__(self, "user_id", self.merchant_id)


class CallbackErrorWithTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="CallbackError", exclude=False)

    transaction_id: str
    merchant_transaction_id: str
    hook_uri: Optional[str] = None
    error: str


class CallbackResponseWithTransactionLogSchema(BasicLogSchema):
    log_name: str = Field(default="CALLBACK", exclude=False)

    transaction_id: str
    merchant_transaction_id: str
    hook_uri: str
    status: int
    response: str