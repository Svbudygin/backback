from fastapi import HTTPException, status as http_status

from app.core.constants import Limit


class MutualExclusiveParamsException(HTTPException):
    def __init__(self, *args):
        super().__init__(
            detail=f"Mutual exclusive filter params provided: {args}", status_code=400
        )


class WrongParamValueException(HTTPException):
    def __init__(self, param, wrong_value):
        super().__init__(
            detail=f"Wrong value {wrong_value} for param {param}.", status_code=400
        )


class TrustBalanceNotEnoughException(HTTPException):
    def __init__(self):
        super().__init__(detail="Not enough trust balance.", status_code=430)


class ProfitBalanceNotEnoughException(HTTPException):
    def __init__(self):
        super().__init__(detail="Not enough profit balance.", status_code=431)


class UserNotEnabledException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="User not enabled. Enable user, if it is impossible, deposit trust balance.",
            status_code=432,
        )


class ExternalTransactionRequestStatusException(HTTPException):
    def __init__(self, statuses):
        super().__init__(
            detail=f'Wrong request external transaction status. Available only for: {", ".join(statuses)}.',
            status_code=433,
        )


class ExternalTransactionExistingStatusException(HTTPException):
    def __init__(self, statuses):
        super().__init__(
            detail=f'Wrong existing external transaction current status. Available only for: {", ".join(statuses)}.',
            status_code=434,
        )


class InternalTransactionRequestStatusException(HTTPException):
    def __init__(self, statuses):
        super().__init__(
            detail=f'Wrong request internal transaction status. Available only for: {", ".join(statuses)}.',
            status_code=435,
        )


class InternalTransactionExistingStatusException(HTTPException):
    def __init__(self, statuses):
        super().__init__(
            detail=f'Wrong existing internal transaction current status. Available only for: {", ".join(statuses)}.',
            status_code=436,
        )


class ExternalTransactionExistingDirectionException(HTTPException):
    def __init__(self, directions):
        super().__init__(
            detail=f'Wrong existing external transaction direction. Available only for: {", ".join(directions)}.',
            status_code=437,
        )


class ExternalTransactionAmountCollisionException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="To much pending transactions for this amount. Accept from platform profile.",
            status_code=438,
        )


class ExternalTransactionCardCollisionException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Can not find card number. Accept from platform profile.",
            status_code=438,
        )

class ExternalTransactionDetailCommentException(HTTPException):
    def __init__(self, comment):
        super().__init__(
            detail=f"Incorrect bank_detail_digits: {comment} or bank_detail.",
            status_code=474,
        )


class ExternalTransactionMessageRepeatedException(HTTPException):
    def __init__(self):
        super().__init__(detail="Message is repeated", status_code=438)


class ExternalTransactionNoCandidatesForAmount(HTTPException):
    def __init__(self):
        super().__init__(
            detail="No external transactions candidates for this amount.",
            status_code=439,
        )


class ExternalTransactionCannotParseAmount(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot parse amount from message", status_code=440)


class WithdrawMinLimitException(HTTPException):
    def __init__(self):
        super().__init__(
            detail=f"Min withdraw limit is currently {Limit.MIN_INTERNAL_OUTBOUND_AMOUNT}",
            status_code=441,
        )


class BankDetailNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find bank detail.", status_code=442)


class CurrencyNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find currency.", status_code=443)


class ExternalTransactionNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find external transaction.", status_code=444)


class InternalTransactionNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find internal transaction.", status_code=445)


class TransactionNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find transaction.", status_code=445)


class UserNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find user.", status_code=446)


class FeeContractNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find contract.", status_code=447)


class TrafficWeightContractNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find contract.", status_code=448)


class TelegramException(HTTPException):
    def __init__(self, detail):
        super().__init__(detail=f"Telegram exception: {detail}", status_code=449)


class AllTeamsDisabledException(HTTPException):
    def __init__(self):
        super().__init__(detail="Cannot find enabled team.", status_code=450)


class InternalTransactionStatusProcessingException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Internal transaction already processing.", status_code=451
        )
class InternalTransactionAcceptStatusWithoutHashException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Internal transaction can't be accept without hash", status_code=468
        )

class PaymentExpiredException(HTTPException):
    def __init__(self):
        super().__init__(detail="Payment expired.", status_code=452)


class FraudDetectedException(HTTPException):
    def __init__(self):
        super().__init__(detail="Fraud detected.", status_code=453)


class UserOrTeamNotContractNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="User or team contract not found.", status_code=454)


class UnableToTransferTransactionException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Unable to transfer external transaction.", status_code=455
        )


class UnableToFindEconomicModel(HTTPException):
    def __init__(self):
        super().__init__(detail="Unable to find economic model.", status_code=456)


class WrongTransactionAmountException(HTTPException):
    def __init__(self):
        super().__init__(detail="Wrong transaction amount.", status_code=457)


class BlockedCardException(HTTPException):
    def __init__(self):
        super().__init__(detail="Blocked card exception.", status_code=458)


class WalletNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Wallet not found.", status_code=459)


class NoOutboundExternalTransactionInPoolException(HTTPException):
    def __init__(self):
        super().__init__(detail="Нет доступных выплат.", status_code=460)


class UserWrongRoleException(HTTPException):
    def __init__(self, roles):
        super().__init__(
            detail=f'Wrong user role. Available only for: {", ".join(roles)}.',
            status_code=403,
        )


class MaxOutboundPendingPerTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Pay the existing payments, then ask for the next ones!",
            status_code=461,
        )


class ExternalTransactionDuplicateMerchantTransactionIdException(HTTPException):
    def __init__(self):
        super().__init__(detail="Duplicate merchant_transaction_id.", status_code=462)


class BalanceNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="balance_id not found by user_id.", status_code=463)


class BankDetailDuplicateException(HTTPException):
    def __init__(self):
        super().__init__(detail="Bank detail is duplicated", status_code=464)


class OnlyOneMerchantTeamException(HTTPException):
    def __init__(self):
        super().__init__(detail="Only one merchant and one team should be", status_code=465)


class WrongTRC20AddressFormatException(HTTPException):
    def __init__(self):
        super().__init__(detail="Wrong trc20 address", status_code=466)


class WrongTypeException(HTTPException):
    def __init__(self):
        super().__init__(detail="Wrong type.", status_code=467)


class ListResponseLengthLimitException(HTTPException):
    def __init__(self):
        super().__init__(
            detail=f"List length not more than {Limit.MAX_ITEMS_PER_QUERY}",
            status_code=416,
        )

class TitleResponseLengthLimitException(HTTPException):
    def __init__(self):
        super().__init__(
            detail=f"Title length not more than {Limit.MAX_STRING_LENGTH_SMALL}",
            status_code=469,
        )


class WrongHashException(HTTPException):
    def __init__(self):
        super().__init__(
            detail=f"Not valid hash",
            status_code=471,
        )

class NotUniqueUserName(HTTPException):
    def __init__(self, user_name):
        super().__init__(
            detail=f"User with name '{user_name}' already exists",
            status_code=472,
        )

class ExternalTransactionHoldLimit(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Выплату нельзя больше продлевать.",
            status_code=473,
        )


class BlockedDepositFromSupports(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Pay out! Deposits are currently block, contact support.",
            status_code=475
        )


class ExistingHashException(HTTPException):
    def __init__(self):
        super().__init__(
            detail=f"Already existing hash",
            status_code=470,
        )


class AppealNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(detail="Appeal not found", status_code=404)


class AppealDecisionAlreadyMadeException(HTTPException):
    def __init__(self):
        super().__init__(detail="Appeal decision already made", status_code=400)


class AppealTransactionNotProvidedException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Either transaction_id or merchant_transaction_id must be provided",
            status_code=400,
        )


class InvalideFileTypeException(HTTPException):
    def __init__(self):
        super().__init__(detail="Uploaded file has invalid type", status_code=400)


class FileSizeException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Uploaded file has exceed maximum file size", status_code=400
        )


class NotEnoughPermissionsException(HTTPException):
    def __init__(self):
        super().__init__(status_code=403)


class UnprocessableEntityException(HTTPException):
    def __init__(self):
        super().__init__(status_code=422)


class AutomaticTestError(HTTPException):
    def __init__(self):
        super().__init__(
            detail=f"Error while testing automatic.", status_code=400
        )


class BankDetailTransactionLimitExceeded(HTTPException):
    def __init__(self):
        super().__init__(
            detail=f"Error Transaction Limit Exceeded", status_code=473
        )


class FileNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=404,
            detail=f"File not found"
        )


class AlreadyUsedHashException(HTTPException):
    def __init__(self, file_name):
        super().__init__(
            detail=f"File {file_name} has already been uploaded within the last month.",
            status_code=476,
        )


class WrongStatusException(HTTPException):
    def __init__(self, statuses):
        super().__init__(
            detail=f'Wrong status. Available only for: {", ".join(statuses)}.',
            status_code=477,
        )


class FeeWillBeNegative(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=478,
            detail=f"Fee would become negative"
        )


class FeeSumException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=479,
            detail=f"Sum of fees will not 100"
        )


class DeleteFeeContractsToBlock(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=480,
            detail="Delete Fee contracts for this user before block"
        )


class BadRequestException(HTTPException):
    def __init__(self, detail):
        super().__init__(
            detail=detail,
            status_code=http_status.HTTP_400_BAD_REQUEST,
        )


class InternalServerErrorException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class TeamNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            detail="Team not found",
            status_code=http_status.HTTP_404_NOT_FOUND,
        )
