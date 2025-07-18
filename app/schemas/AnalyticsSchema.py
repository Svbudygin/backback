from app.schemas.BaseScheme import BaseScheme


class PowerBIResponseSchema(BaseScheme):
    embedToken: str
    reportId: str
    embedUrl: str
