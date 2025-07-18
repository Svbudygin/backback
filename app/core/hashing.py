import json
from collections.abc import Callable
from hashlib import sha256
from hmac import HMAC
from hmac import new as hmac_new



def hash_message(message: str | bytes, hash_method: Callable = sha256, secret_key: str | bytes = "") -> HMAC:
    """
    Hash message with secret key.

    :param message: Message to hash.
    :param hash_method: Hash method to use. Default: sha256.
    :param secret_key: Secret key to use. Default: ''.

    :return: HMAC object.
    """
    return hmac_new(
        key=secret_key if isinstance(secret_key, bytes) else secret_key.encode(),
        msg=message if isinstance(message, bytes) else message.encode(),
        digestmod=hash_method,
    )


def check_signature(request: Request, secret_key: str, sent_signature: str) -> bool:
    raw_body_hash = hash_message(message=request.body, secret_key=secret_key).hexdigest()
    
    data: dict = {}
    for key, value in request.data.items():
        if not isinstance(value, InMemoryUploadedFile):
            data[key] = value
    
    raw_data_hash = hash_message(message=json.dumps(data), secret_key=secret_key).hexdigest()
    
    stringify_data_hash = hash_message(
        message=json.dumps(data, separators=(",", ":")), secret_key=secret_key
    ).hexdigest()
    
    return (
            raw_data_hash == sent_signature
            or stringify_data_hash == sent_signature
            or raw_body_hash == sent_signature
    )