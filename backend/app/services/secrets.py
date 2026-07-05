import base64
import hashlib

from app.core.config import settings


class SecretEncryptionService:
    """TODO: replace with authenticated encryption before production use."""

    def __init__(self, key: str | None = None) -> None:
        self._key = hashlib.sha256((key or settings.secret_key).encode("utf-8")).digest()

    def encrypt(self, plaintext: str) -> bytes:
        payload = plaintext.encode("utf-8")
        encrypted = bytes(byte ^ self._key[index % len(self._key)] for index, byte in enumerate(payload))
        return base64.urlsafe_b64encode(encrypted)

    def decrypt(self, ciphertext: bytes) -> str:
        encrypted = base64.urlsafe_b64decode(ciphertext)
        payload = bytes(byte ^ self._key[index % len(self._key)] for index, byte in enumerate(encrypted))
        return payload.decode("utf-8")


def get_secret_encryption_service() -> SecretEncryptionService:
    return SecretEncryptionService()
