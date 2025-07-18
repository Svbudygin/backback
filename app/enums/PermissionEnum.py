from enum import Enum


class Permission(Enum):
    VIEW_TRAFFIC = 'view_traffic'
    VIEW_FEE = 'view_fee'
    VIEW_PAY_IN = 'view_pay_in'
    VIEW_PAY_OUT = 'view_pay_out'
    VIEW_TEAMS = 'view_teams'
    VIEW_MERCHANTS = 'view_merchants'
    VIEW_AGENTS = 'view_agents'
    VIEW_WALLET = 'view_wallet'
    VIEW_SUPPORTS = 'view_supports'
    VIEW_SEARCH = 'view_search'
    VIEW_COMPENSATIONS = 'view_compensations'
    VIEW_SMS_HUB = 'view_sms_hub'
    VIEW_ACCOUNTING = 'view_accounting'
    VIEW_DETAILS = 'view_details'
    VIEW_APPEALS = 'view_appeals'
    VIEW_ANALYTICS = 'view_analytics'
