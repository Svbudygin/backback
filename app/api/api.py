from fastapi import APIRouter

from app.api.routes import (
    backup,
    bank_detail,
    contract,
    data,
    export_transactions,
    external_transaction,
    internal_transaction,
    payment_form,
    root,
    statistics,
    temp,
    user,
    devices,
    payment_link,
    message,
    file,
    info,
    filters,
    analytics,
    settings
)
from app.api.routes.admin import (
    agent_routes,
    support_routes,
    fee_contracts,
    merchant_routes,
    namespace,
    team_routes,
    geo_routes,
    traffic_weight_routes,
    tags,
    roles,
    bank_detail_routes,
    accounting_routes
)
from app.api.routes.v2 import appeal
from app.api.routes.v2 import external_transaction as v2_external_transaction
from app.api.routes.v2 import payment_form as v2_payment_form

api_router = APIRouter()
api_router.include_router(data.router, prefix="/data", tags=["Data [*]"])
api_router.include_router(temp.router, prefix="/temp", tags=["Temporary"])
api_router.include_router(
    user.router, prefix="/user", tags=["User [Agent, Merchant, Root, Team, Support]"]
)
api_router.include_router(
    statistics.router,
    prefix="/statistics",
    tags=["Statistics [Agent, Merchant, Root, Team]"],
)
api_router.include_router(
    bank_detail.router, prefix="/bank_detail", tags=["Bank detail [Team]"]
)

api_router.include_router(
    payment_form.router, prefix="/payment-form", tags=["Payment form [Merchant]"]
)

api_router.include_router(
    external_transaction.router,
    prefix="/external-transaction",
    tags=["External transaction [Merchant, Root, Team]"],
)

api_router.include_router(
    message.router, prefix="/message", tags=["Message [Team, Support]"]
)

api_router.include_router(
    namespace.router, prefix="/admin/namespace", tags=["Admin for namespace [Support]"]
)

api_router.include_router(
    accounting_routes.router, prefix="/admin/accounting", tags=["Admin for accounting [Support]"]
)
api_router.include_router(
    tags.router, prefix="/admin/tags", tags=["Admin for tags [Support]"]
)
api_router.include_router(
    roles.router,
    prefix="/admin/roles",
    tags=["Admin for roles"]
)
api_router.include_router(
    geo_routes.router,
    prefix="/admin/geo",
    tags=["Admin for geo"]
)
api_router.include_router(
    fee_contracts.router,
    prefix="/admin/fee-contracts",
    tags=["Admin for fee contracts [Support]"],
)
api_router.include_router(
    traffic_weight_routes.router,
    prefix="/admin/traffic-weight-routes",
    tags=["Admin for traffic weight routes [Support]"],
)
api_router.include_router(
    team_routes.router,
    prefix="/admin/team",
    tags=["Admin for Teams [Support]"],
)
api_router.include_router(
    merchant_routes.router,
    prefix="/admin/merchant",
    tags=["Admin for Merchants [Support]"],
)
api_router.include_router(
    agent_routes.router,
    prefix="/admin/agent",
    tags=["Admin for Agents [Support]"],
)
api_router.include_router(
    support_routes.router,
    prefix="/admin/support",
    tags=["Admin for Supports [Support]"],
)
api_router.include_router(
    bank_detail_routes.router,
    prefix="/admin/details",
    tags=["Admin for Details [Support]"],
)
api_router.include_router(
    v2_external_transaction.router,
    prefix="/merchant",
    tags=["Merchant H2H integration API"],
)
api_router.include_router(appeal.router, prefix="/v2/appeal", tags=["Merchant"])
api_router.include_router(
    internal_transaction.router,
    prefix="/internal-transaction",
    tags=["Internal transaction [Agent, Merchant, Root, Team]"],
)
api_router.include_router(
    export_transactions.router,
    prefix="/export",
    tags=["Export transactions [Merchant]"],
)

api_router.include_router(root.router, prefix="/create", tags=["Create user [Root]"])

api_router.include_router(
    contract.fee_router, prefix="/contract/fee", tags=["Fee contract [Root]"]
)
api_router.include_router(
    contract.traffic_weight_router,
    prefix="/contract/traffic-weight",
    tags=["Traffic weight contract [Root]"],
)
api_router.include_router(
    backup.router, prefix="/system", tags=["Be careful! Don't do it!"]
)

api_router.include_router(
    devices.router,
    prefix="/devices",
    tags=["Devices"],
)

api_router.include_router(
    payment_link.router,
    prefix="/payment-link",
    tags=["Payment links"]
)

api_router.include_router(
    v2_payment_form.router,
    prefix="/v2/payment-form",
    tags=["Payment form v2"],
)

api_router.include_router(
    file.router,
    prefix="/file",
    tags=["File"]
)

api_router.include_router(
    info.router,
    prefix="/info",
    tags=["Info"]
)

api_router.include_router(
    filters.router,
    prefix="/filters",
    tags=["Filters"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

api_router.include_router(
    settings.router,
    prefix="/settings",
    tags=["Settings"]
)
