"""Authentication primitives; no credential is returned to browser settings."""
import hashlib
from argon2 import PasswordHasher, Type, extract_parameters
from argon2.exceptions import InvalidHashError, VerificationError

PASSWORD_HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, type=Type.ID)


def validate_admin_hash(encoded):
    try:
        parameters = extract_parameters(encoded)
        if (parameters.type != Type.ID or parameters.version != 19 or
                not 19456 <= parameters.memory_cost <= 262144 or
                not 2 <= parameters.time_cost <= 6 or
                not 1 <= parameters.parallelism <= 8 or
                parameters.salt_len < 16 or parameters.hash_len < 16):
            raise ValueError()
    except (InvalidHashError, ValueError, TypeError):
        raise RuntimeError('Cần hash mật khẩu Argon2id hợp lệ; tạo lại bằng tools/hash_admin_password.py.') from None


def verify_admin_password(encoded, password):
    if not isinstance(password, str) or not 1 <= len(password) <= 256:
        return False
    try:
        return PASSWORD_HASHER.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def token_digest(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
