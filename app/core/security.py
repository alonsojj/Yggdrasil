import hashlib
import base64
import hmac
from app.core.config import get_settings

PROXY_SECRET_KEY = bytes(get_settings().secret_key, "utf-8")


def sign_path(path: str) -> str:
    signature = hmac.new(PROXY_SECRET_KEY, path.encode(), hashlib.sha256).hexdigest()
    return signature[:12]


def encode_url_path(path: str) -> str:
    return base64.urlsafe_b64encode(path.encode()).decode()


def decode_url_path(encoded_path: str) -> str:
    return base64.urlsafe_b64decode(encoded_path).decode()
