from app.schemas.BaseScheme import BaseScheme


class InfoSummaryResponseSchema(BaseScheme):
    pending_appeals: int
    pending_pay_outs: int
    total_pay_outs: int
