from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError

from profile.application.utils import generate_jwt_token, decode_token
from profile.exceptions import BadCredentialsError, DecodeTokenError
from profile.repository import ProfileRepository

oauth2_scheme = OAuth2PasswordBearer('token')


class ProfileService:

    def __init__(self, repo: ProfileRepository = Depends()):
        self._repo = repo

    def authorize_user(self, username: str, password: str) -> str | None:
        user = self._repo.get_by_username(username)

        if user is None:
            raise BadCredentialsError

        data = {'id': str(user._id), 'username': user.username}
        token = generate_jwt_token(password, user.password, data)

        if token is None:
            raise BadCredentialsError
        return token

    @staticmethod
    def get_user_from_token(token: str = Depends(oauth2_scheme)):
        try:
            return decode_token(token)
        except ExpiredSignatureError:
            raise DecodeTokenError('Authorization token has expired')
        except JWTError:
            raise DecodeTokenError('Invalid token authorization')
