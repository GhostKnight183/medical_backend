from fastapi import Response
from core import jwt_aes_settings as aes_settings
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
import bcrypt


def hash_pass(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def check_pass(hash_pass: bytes, password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hash_pass)


def set_cookie(response: Response, key: str, value: str, max_age: int):
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=max_age
    )


encoded_key_str = aes_settings.aes_key.read_text().strip()
AES_KEY = base64.b64decode(encoded_key_str.encode())
aesgcm = AESGCM(AES_KEY)


def encrypt(token: str):
    nonce = os.urandom(12)
    token_bytes = token.encode()
    encrypted = aesgcm.encrypt(nonce, token_bytes, None)
    return base64.b64encode(nonce + encrypted)


def decrypt(encrypted_64: str | bytes):
    if isinstance(encrypted_64, bytes):
        encrypted_64 = encrypted_64.decode("utf-8")

    if encrypted_64.startswith("b'") and encrypted_64.endswith("'"):
        encrypted_64 = encrypted_64[2:-1]

    raw = base64.b64decode(encrypted_64)
    nonce, ciphertext = raw[:12], raw[12:]
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted.decode()