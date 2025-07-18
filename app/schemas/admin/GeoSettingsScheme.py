from pydantic import ConfigDict
from app.schemas.BaseScheme import BaseScheme, num_factory


class UpdateGeoSettings(BaseScheme):
    max_outbound_pending_per_token: int | None = num_factory(None)
    max_count_hold: int | None = num_factory(None)
    get_back_transactions_time_s: int | None = num_factory(None)
    max_transfer_count: int | None = num_factory(None)
    max_inbound_close_count: int | None = num_factory(None)
    block_deposit: bool | None = num_factory(None)
    auto_close_outbound_transactions_s: int | None = num_factory(None)
    req_after_enable_max_pay_in_count: int | None = num_factory(None)
    req_after_enable_max_pay_in_automation_time: int | None = num_factory(None)


class ResponseUpdateGeoSettings(BaseScheme):
    model_config = ConfigDict(from_attributes=True)

    id: int = num_factory()
    max_outbound_pending_per_token: int = num_factory()
    max_count_hold: int = num_factory()
    get_back_transactions_time_s: int = num_factory()
    max_transfer_count: int = num_factory()
    max_inbound_close_count: int = num_factory()
    auto_close_outbound_transactions_s: int = num_factory()
    req_after_enable_max_pay_in_count: int = num_factory()
    req_after_enable_max_pay_in_automation_time: int = num_factory()
    block_deposit: bool

