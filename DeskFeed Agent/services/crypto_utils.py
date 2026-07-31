import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_SALT = b'deskfeed_salt_2024'
_KEY = None

def _get_key():
    global _KEY
    if _KEY is None:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=100000)
        key = base64.urlsafe_b64encode(kdf.derive(b'deskfeed_secret_key'))
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
