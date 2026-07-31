import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from config import CRYPTO_SECRET

_SALT = b'deskfeed_salt_2024'
_KEY = None

def _get_key():
    global _KEY
    if _KEY is None:
        secret = CRYPTO_SECRET.encode() if CRYPTO_SECRET else os.urandom(32)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(secret))
        _KEY = key
    return _KEY

def encrypt_payload(data_str: str) -> str:
    key = _get_key()
    f = Fernet(key)
    return f.encrypt(data_str.encode()).decode()

def decrypt_payload(token: str) -> str:
    key = _get_key()
    f = Fernet(key)
    return f.decrypt(token.encode()).decode()
