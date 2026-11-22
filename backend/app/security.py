
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)



import secrets
import hashlib


def generate_verification_code() -> str:
    return str(secrets.randbelow(1000000)).zfill(6)


def hash_verification_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()



from datetime import datetime, timedelta, timezone
import jwt

from app.database import settings


def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt