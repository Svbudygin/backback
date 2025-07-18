import base64
import json
from cryptography.fernet import Fernet
from fastapi import HTTPException

XOR_SECRET_KEY = b"gmfalkjgla=431ou413lfadns"
FERNET_SECRET_KEY = b'WlO2N45QtmcSPmO7BWrt1utoK8k-ItzryQNdXnMBRds='
fernet = Fernet(FERNET_SECRET_KEY)


def encrypt_fernet(data: dict) -> str:
    data = json.dumps(data)
    encrypted_data = fernet.encrypt(data.encode())

    return base64.urlsafe_b64encode(encrypted_data).decode()


def decrypt_fernet(encoded_string: str) -> dict:
    try:
        encrypted_data = base64.urlsafe_b64decode(encoded_string)
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return json.loads(decrypted_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid data")


def encrypt_base64_with_key(plain_text) -> str:
    plain_text_bytes = plain_text.encode("utf-8")
    encrypted_bytes = bytearray()
    for i, byte in enumerate(plain_text_bytes):
        encrypted_bytes.append(byte ^ XOR_SECRET_KEY[i % len(XOR_SECRET_KEY)])
    return base64.b64encode(encrypted_bytes).decode("utf-8")
