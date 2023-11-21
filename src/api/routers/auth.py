from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from profile.application import ProfileService

router = APIRouter()


@router.post('/token')
def auth(form_data: OAuth2PasswordRequestForm = Depends(),
         user_service: ProfileService = Depends()):
    jwt_token = user_service.authorize_user(form_data.username, form_data.password)
    return {'token_type': 'Bearer', 'access_token': jwt_token}
