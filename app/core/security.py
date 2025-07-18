"""Black-box security shortcuts to generate JWT tokens and password hashing and verifcation."""
import base64
import secrets
import time

import jwt
from passlib.context import CryptContext
from passlib.handlers import bcrypt
from pydantic import BaseModel

from app.core import config
from app.schemas.UserScheme import AuthSchemeAccessTokenResponse

import bcrypt

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECS = config.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_TOKEN_EXPIRE_SECS = config.settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=config.settings.SECURITY_BCRYPT_ROUNDS,
)


class JWTTokenPayload(BaseModel):
    subject: str | int
    refresh: bool
    issued_at: int
    expires_at: int


class PaymentJWTTokenPayload(BaseModel):
    user_role: str
    merchant_id: str
    payer_id: str
    refresh: bool
    issued_at: int
    expires_at: int
    amount: int
    currency_id: str
    merchant_transaction_id: str
    hook_uri: str | None = None


def create_jwt_token(exp_secs: int, refresh: bool, **kwargs):
    """Creates jwt access or refresh token for user.

    Args:
        subject: anything unique to user, id or email etc.
        exp_secs: expire time in seconds
        refresh: if True, this is refresh token
    """
    
    issued_at = int(time.time())
    expires_at = issued_at + exp_secs
    
    to_encode: dict[str, int | str | bool] = {
        "issued_at": issued_at,
        "expires_at": expires_at,
        "refresh": refresh,
        **kwargs
    }
    encoded_jwt = jwt.encode(
        to_encode,
        key=config.settings.SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )
    return encoded_jwt, expires_at, issued_at


def generate_access_token_response(role: str,
                                   access_token_expires_s: int = ACCESS_TOKEN_EXPIRE_SECS,
                                   refresh_token_expires_s: int = REFRESH_TOKEN_EXPIRE_SECS,
                                   **kwargs
                                   ):
    """Generate tokens and return AccessTokenResponse"""
    access_token, expires_at, issued_at = create_jwt_token(
        exp_secs=access_token_expires_s, refresh=False, **kwargs
    )
    refresh_token, refresh_expires_at, refresh_issued_at = create_jwt_token(
        exp_secs=refresh_token_expires_s, refresh=True, **kwargs
    )
    return AuthSchemeAccessTokenResponse(
        token_type="Bearer",
        access_token=access_token,
        expires_at=expires_at,
        issued_at=issued_at,
        refresh_token=refresh_token,
        refresh_token_expires_at=refresh_expires_at,
        refresh_token_issued_at=refresh_issued_at,
        role=role
    )


def get_password_hash(password: str) -> str:
    decoded: bytes = base64.b64decode(config.settings.SECRET_HASH_KEY)
    return bcrypt.hashpw(password.encode('utf-8'), salt=decoded).decode()


def generate_password() -> str:
    return str(secrets.token_hex(32))


def generate_device_token() -> str:
    return f'device{str(secrets.token_hex(32))}'

if __name__ == "__main__":
    password = generate_password()
    print(password, get_password_hash(password))
    #проверка