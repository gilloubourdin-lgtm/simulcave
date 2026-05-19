# app/services/auth.py

from passlib.context import CryptContext
from itsdangerous import URLSafeSerializer, BadSignature

SECRET_KEY = "change-this-secret-key-in-production"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
serializer = URLSafeSerializer(SECRET_KEY, salt="simulcave-session")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_session_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def decode_session_token(token: str) -> int | None:
    try:
        data = serializer.loads(token)
        return data.get("user_id")
    except BadSignature:
        return None