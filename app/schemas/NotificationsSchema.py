from typing import TypeVar
from enum import Enum

from app.schemas.BaseScheme import BaseScheme


class NotificationTypeEnum(Enum):
    DEVICE_DISCONNECTED = 'REQ_DISABLED'
    MANY_CLOSE_DISABLE = 'REQ_CLOSE_DISABLED'
    NEW_APPEAL = 'NEW_APPEAL'
    BLOCKED_DEVICE = 'REQ_BLOCKED'
    REQ_INCORRECT_WORKING = 'REQ_INCORRECT_WORKING'
    LOW_BALANCE = 'LOW_BALANCE'
    ENABLE_REQ_FOR_FILL = 'ENABLE_REQ_FOR_FILL'
    DISABLE_REQ_FOR_FILL = 'DISABLE_REQ_FOR_FILL'


class AbstractNotificationSchema(BaseScheme):
    event_type: NotificationTypeEnum

class BaseNotificationSchema(AbstractNotificationSchema):
    team_id: str

class BaseSupportNotificationSchema(AbstractNotificationSchema):
    support_id: str

NotificationSchema = TypeVar('NotificationSchema', bound=AbstractNotificationSchema)


class ReqDisabledNotificationDataSchema(BaseScheme):
    number: str


class NewAppealNotificationDataSchema(BaseScheme):
    link: str


class LowBalanceNotificationDataSchema(BaseScheme):
    limit: int


class ReqDisabledNotificationSchema(BaseNotificationSchema):
    event_type: str = NotificationTypeEnum.DEVICE_DISCONNECTED

    data: ReqDisabledNotificationDataSchema


class ReqCloseDisabledNotificationSchema(BaseNotificationSchema):
    event_type: str = NotificationTypeEnum.MANY_CLOSE_DISABLE

    data: ReqDisabledNotificationDataSchema


class NewAppealNotificationSchema(BaseNotificationSchema):
    event_type: str = NotificationTypeEnum.NEW_APPEAL

    data: NewAppealNotificationDataSchema


class ReqBlockedNotificationSchema(BaseNotificationSchema):
    event_type: str = NotificationTypeEnum.BLOCKED_DEVICE

    data: ReqDisabledNotificationDataSchema


class ReqIncorrectWorkingNotificationSchema(BaseNotificationSchema):
    event_type: str = NotificationTypeEnum.REQ_INCORRECT_WORKING

    data: ReqDisabledNotificationDataSchema


class LowBalanceNotificationSchema(BaseNotificationSchema):
    event_type: str = NotificationTypeEnum.LOW_BALANCE

    data: LowBalanceNotificationDataSchema


class EnableReqForFillSupportNotificationSchema(BaseSupportNotificationSchema):
    event_type: str = NotificationTypeEnum.ENABLE_REQ_FOR_FILL

    data: ReqDisabledNotificationDataSchema


class DisableReqForFillSupportNotificationSchema(BaseSupportNotificationSchema):
    event_type: str = NotificationTypeEnum.DISABLE_REQ_FOR_FILL

    data: ReqDisabledNotificationDataSchema


class TeamStatementReceivedSchema(BaseModel):
    """Уходит сапорту, когда команда загрузила выписку по отклонённой апелляции."""
    appeal_id: str
    transaction_id: str
    merchant_transaction_id: Optional[str] = None
    merchant_appeal_id: Optional[str] = None
    reject_reason: Optional[str] = None      # чтобы сапорт видел, почему отклоняли
    file_ids: List[str]  
