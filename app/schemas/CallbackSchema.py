from typing import Optional, TypeVar

from app.schemas.BaseScheme import BaseScheme


class BaseCallbackSchema(BaseScheme):
    name: str


CallbackSchema = TypeVar('CallbackSchema', bound=BaseCallbackSchema)


class AppealMerchantStatementRequiredCallbackSchema(BaseCallbackSchema):
    name: str = 'AppealMerchantStatementRequired'

    id: str
    transaction_id: str
    merchant_appeal_id: Optional[str] = None
    merchant_transaction_id: Optional[str] = None


class AppealFinalizationCallbackSchema(BaseCallbackSchema):
    name: str = 'AppealFinalization'

    id: str
    transaction_id: str
    merchant_transaction_id: Optional[str] = None
    merchant_appeal_id: Optional[str] = None
    new_amount: int
    status: str
    code: Optional[str] = None

