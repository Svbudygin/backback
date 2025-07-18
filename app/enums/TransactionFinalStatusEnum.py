from enum import Enum


class TransactionFinalStatusEnum(Enum):
    AUTO = 'auto'
    ACCEPT = 'accept'
    APPEAL = 'appeal'
    RECALC = 'recalc'
    TIMEOUT = 'timeout'
    CANCEL = 'cancel'
