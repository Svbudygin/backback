from app.schemas.BaseScheme import BaseScheme, num_factory, str_small_factory


class UpdateCurrencyRequest(BaseScheme):
    id: str = str_small_factory()
    inbound_exchange_rate: int = num_factory()
    outbound_exchange_rate: int = num_factory()


class UpdateCurrencyResponse(UpdateCurrencyRequest):
    name: str = str_small_factory()


class BalanceStatsResponse(BaseScheme):
    trust_balance: int = num_factory()
    locked_balance: int = num_factory()
    fiat_trust_balance: int = num_factory()
    fiat_locked_balance: int = num_factory()
    inbound_fiat_profit_balance: int = num_factory()
    outbound_profit_balance: int = num_factory()