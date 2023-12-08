from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext


SECRET_KEY = 'ff9dff1e554384040b0989aef9835773c770c867a0f6d5a810edfb656ff76758'
ALGORITHM = 'HS256'
crypt_context = CryptContext(['bcrypt'])


def generate_jwt_token(input_password: str,
                       actual_password: str,
                       data: dict) -> str | None:
    if crypt_context.verify(input_password, actual_password):
        expire = datetime.utcnow() + timedelta(weeks=1)
        data['exp'] = expire
        return jwt.encode(data, SECRET_KEY, ALGORITHM)


async def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, ALGORITHM)


def hash_password(password: str) -> str:
    return crypt_context.hash(password)
