from typing import Union
from enum import Enum
from sqlalchemy import and_, or_

from app.schemas.AppealScheme import AppealCloseCodeEnum
from app.models import AppealModel, ExternalTransactionModel
from app.core.constants import StatusEnum, BaseEnum


class SupportCategoriesEnum(str, BaseEnum):
    PENDING = 'pending'
    NEED_TO_FINALIZE = 'need-to-finalize'
    HISTORY = 'history'
    MERCHANT_STATEMENT = 'merchant-statement'
    TEAM_STATEMENT = 'team-statement'
    NEED_TO_FINALIZE_PENDING = 'need-to-finalize-pending'
    NEED_TO_FINALIZE_MERCHANT_STATEMENT = 'need-to-finalize-merchant-statement'
    NEED_TO_FINALIZE_TEAM_STATEMENT = 'need-to-finalize-team-statement'
    NEED_TO_FINALIZE_TIMEOUT = 'need-to-finalize-timeout'


class TeamCategoriesEnum(str, BaseEnum):
    PENDING = 'pending'
    HISTORY = 'history'
    MERCHANT_STATEMENT = 'merchant-statement'
    TEAM_STATEMENT = 'team-statement'
    WAIT_DECISION = 'wait-decision'


SUPPORT_CATEGORIES = [
    [
        {
            "title": "Need to finalize",
            "code": SupportCategoriesEnum.NEED_TO_FINALIZE,
            "children": [
                [
                    {
                        "title": "Pending",
                        "code": SupportCategoriesEnum.NEED_TO_FINALIZE_PENDING,
                        "children": []
                    },
                    {
                        "title": "Merchant statement",
                        "code": SupportCategoriesEnum.NEED_TO_FINALIZE_MERCHANT_STATEMENT,
                        "children": []
                    },
                    {
                        "title": "Team statement",
                        "code": SupportCategoriesEnum.NEED_TO_FINALIZE_TEAM_STATEMENT,
                        "children": []
                    }
                ],
                [
                    {
                        "title": "Timeout",
                        "code": SupportCategoriesEnum.NEED_TO_FINALIZE_TIMEOUT,
                        "children": []
                    }
                ]
            ]
        },   
        {
            "title": "Pending",
            "code": SupportCategoriesEnum.PENDING,
            "children": []
        }
    ],
    [
        {
            "title": "Merchant statement",
            "code": SupportCategoriesEnum.MERCHANT_STATEMENT,
            "children": []
        },
        {
            "title": "Team statement",
            "code": SupportCategoriesEnum.TEAM_STATEMENT,
            "children": []
        }
    ],
    [
        {
            "title": "History",
            "code": SupportCategoriesEnum.HISTORY,
            "children": []
        }
    ]
]

TEAM_CATEGORIES = [
    [
        {
            "title": "Ожидание",
            "code": TeamCategoriesEnum.PENDING
        },
        {
            "title": "Ожидает решения",
            "code": TeamCategoriesEnum.WAIT_DECISION
        }
    ],
    [
        {
            "title": "Выписка мерчанта",
            "code": TeamCategoriesEnum.MERCHANT_STATEMENT
        },
        {
            "title": "Выписка команды",
            "code": TeamCategoriesEnum.TEAM_STATEMENT
        }
    ],
    [
        {
            "title": "История",
            "code": TeamCategoriesEnum.HISTORY
        }
    ]
]

APPEAL_NOT_CLOSED_CONDITION = and_(
    ExternalTransactionModel.status != StatusEnum.ACCEPT,
    or_(
        AppealModel.is_support_confirmation_required == True,
        AppealModel.reject_reason == None
    )
)

APPEAL_FINALIZED_CONDITION = or_(
    ExternalTransactionModel.status == StatusEnum.ACCEPT,
    and_(
        AppealModel.reject_reason != None,
        AppealModel.is_support_confirmation_required == False
    )
)

SUPPORT_CATEGORIES_FILTERS = {
    SupportCategoriesEnum.PENDING: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_merchant_statement_required == False,
            AppealModel.is_team_statement_required == False,
            AppealModel.is_support_confirmation_required == False
        )
    ],
    SupportCategoriesEnum.NEED_TO_FINALIZE: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_support_confirmation_required == True
        )
    ],
    SupportCategoriesEnum.MERCHANT_STATEMENT: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_merchant_statement_required == True
        )
    ],
    SupportCategoriesEnum.TEAM_STATEMENT: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_team_statement_required == True
        )
    ],
    SupportCategoriesEnum.HISTORY: [
        APPEAL_FINALIZED_CONDITION
    ],
    SupportCategoriesEnum.NEED_TO_FINALIZE_PENDING: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            or_(
                AppealModel.merchant_statements == None,
                AppealModel.merchant_statements == []
            ),
            or_(
                AppealModel.team_statements == None,
                AppealModel.team_statements == []
            ),
            AppealModel.is_support_confirmation_required == True
        )
    ],
    SupportCategoriesEnum.NEED_TO_FINALIZE_MERCHANT_STATEMENT: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            and_(
                AppealModel.merchant_statements != None,
                AppealModel.merchant_statements != []
            ),
            or_(
                AppealModel.team_statements == None,
                AppealModel.team_statements == []
            ),
            AppealModel.is_support_confirmation_required == True
        )
    ],
    SupportCategoriesEnum.NEED_TO_FINALIZE_TEAM_STATEMENT: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            and_(
                AppealModel.merchant_statements != None,
                AppealModel.merchant_statements != []
            ),
            and_(
                AppealModel.team_statements != None,
                AppealModel.team_statements != []
            ),
            AppealModel.is_support_confirmation_required == True
        )
    ],
    SupportCategoriesEnum.NEED_TO_FINALIZE_TIMEOUT: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.timeout_expired == True
        )
    ]
}

TEAM_CATEGORIES_FILTERS = {
    TeamCategoriesEnum.PENDING: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_merchant_statement_required == False,
            AppealModel.is_team_statement_required == False,
            AppealModel.is_support_confirmation_required == False
        )
    ],
    TeamCategoriesEnum.MERCHANT_STATEMENT: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_merchant_statement_required == True
        )
    ],
    TeamCategoriesEnum.TEAM_STATEMENT: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_team_statement_required == True
        )
    ],
    TeamCategoriesEnum.WAIT_DECISION: [
        and_(
            APPEAL_NOT_CLOSED_CONDITION,
            AppealModel.is_support_confirmation_required == True
        )
    ],
    TeamCategoriesEnum.HISTORY: [
        APPEAL_FINALIZED_CONDITION
    ]
}

CATEGORIES_PARAM = Union[SupportCategoriesEnum, TeamCategoriesEnum]

APPEAL_REJECT_REASON_TITLES = {
    AppealCloseCodeEnum.incorrect_reqs.value: {
        "ru": "Не совпадают реквизиты",
        "en": "Incorrect bank details"
    },
    AppealCloseCodeEnum.closed_another_transaction.value: {
        "ru": "Закрыло другую заявку",
        "en": "Closed another transaction"
    },
    AppealCloseCodeEnum.fake_receipt.value: {
        "ru": "Поддельный чек",
        "en": "Fake receipt"
    },
    AppealCloseCodeEnum.timeout.value: {
        "ru": "Таймаут",
        "en": "Timeout",
        "is_private": True
    }
}

APPEAL_REJECT_REASONS = [
    AppealCloseCodeEnum.incorrect_reqs,
    AppealCloseCodeEnum.closed_another_transaction
]

APPEAL_SUPPORT_REJECT_REASONS = APPEAL_REJECT_REASONS + [
    AppealCloseCodeEnum.fake_receipt
]
