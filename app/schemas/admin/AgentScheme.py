from typing import Optional

from app.schemas.BaseScheme import BaseScheme
from app.schemas.UserScheme import UserScheme


class CreateAgentRequestScheme(BaseScheme):
    name: str


class UpdateAgentRequestScheme(BaseScheme):
    is_blocked: bool = None


class AgentResponseScheme(BaseScheme):
    id: str
    name: str
    trust_balance: int = 0
    is_blocked: bool
    password: str | None = None


class V2AgentResponseScheme(UserScheme):
    trust_balance: int = 0
    password: Optional[str] = None
