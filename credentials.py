"""Encrypt cloud connection keys before storing them in Neon settings."""
import base64
import hashlib


def cipher(secret):
    from cryptography.fernet import Fernet
    key = hashlib.sha256(('attendsift-connections-v1|' + secret).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def seal(value, secret):
    return cipher(secret).encrypt(value.encode()).decode()


def unseal(value, secret):
    from cryptography.fernet import InvalidToken
    try:
        return cipher(secret).decrypt(value.encode()).decode()
    except (InvalidToken, ValueError, UnicodeError):
        return ''
