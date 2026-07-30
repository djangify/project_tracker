# ai_settings/encryption.py
"""Symmetric encryption for API keys stored in the local SQLite file.

The key is derived from Django's SECRET_KEY, so the same install that owns the
database can decrypt its own keys without any extra secret to manage — which
suits a single-user, self-hosted download. If SECRET_KEY changes, previously
stored API keys can no longer be decrypted and must be re-entered.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet:
    # Fernet needs a 32-byte urlsafe-base64 key; derive one deterministically
    # from SECRET_KEY with SHA-256.
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        # SECRET_KEY changed or the stored value is corrupt/plaintext.
        return ""
