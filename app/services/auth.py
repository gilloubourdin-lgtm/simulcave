# app/services/auth.py

import os
from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer, BadSignature, SignatureExpired


SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret-key-change-me")

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

session_serializer = URLSafeSerializer(
    SECRET_KEY,
    salt="simulcave-session",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_password_hash(password: str) -> str:
    return hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_session_token(user_id: int) -> str:
    return session_serializer.dumps({"user_id": user_id})


def decode_session_token(token: str) -> int | None:
    try:
        data = session_serializer.loads(token)
        return data.get("user_id")
    except BadSignature:
        return None


def get_reset_serializer():
    return URLSafeTimedSerializer(SECRET_KEY)


def create_password_reset_token(email: str) -> str:
    serializer = get_reset_serializer()
    return serializer.dumps(email, salt="password-reset")


def verify_password_reset_token(token: str, max_age_seconds: int = 3600):
    serializer = get_reset_serializer()

    try:
        return serializer.loads(
            token,
            salt="password-reset",
            max_age=max_age_seconds,
        )
    except SignatureExpired:
        return None
    except BadSignature:
        return None