import bcrypt
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:

    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        logger.warning(
            f"Password length ({len(password_bytes)} bytes)9"
            f" exceeds bcrypt limit, will be truncated to 72 bytes"
        )

    salt = bcrypt.gensalt(rounds=14)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:

    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
