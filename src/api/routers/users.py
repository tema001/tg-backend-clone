from fastapi import APIRouter, Body, Depends, status
from fastapi.exceptions import HTTPException

from conversations.domain.entity import ConversationEntity
from conversations.repository import ConversationRepository
from profile.application import ProfileService
from profile.domain.entity import ProfileEntity
from profile.repository import ProfileRepository

from shared import idType
from api.schemas import ConversationResponse, UserInfoResponse

router = APIRouter()


@router.post('/register', status_code=status.HTTP_201_CREATED)
def register_new_user(profile_repo: ProfileRepository = Depends(),
                      new_user: dict = Body()):
    profile = ProfileEntity.create(new_user['username'], new_user['password'])
    profile_repo.add(profile)

    return str(profile._id)


@router.post('/contact/{contact_id}/chat')
def new_conversation(contact_id: str,
                     user: dict = Depends(ProfileService.get_user_from_token),
                     conv_repo: ConversationRepository = Depends()):
    if user['id'] == contact_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail='The User ID and contact ID are the same')

    myself, contact = idType(user['id']), idType(contact_id)
    conv = conv_repo.find_private_by_ids(myself, contact)
    if conv:
        return str(conv._id)

    conv = ConversationEntity.create('private', (myself, contact))
    conv_repo.add(conv)

    return str(conv._id)


@router.get('/info/me')
def get_conversations(user: dict = Depends(ProfileService.get_user_from_token),
                      profile_repo: ProfileRepository = Depends(),
                      conv_repo: ConversationRepository = Depends()):
    user_id = user['id']
    profile = profile_repo.get_by_id(idType(user_id))
    conv = conv_repo.find_all_detailed_by_participant_id(idType(user_id))

    convs_resp = [ConversationResponse(user_id, my_conv) for my_conv in conv]

    return UserInfoResponse(id=user_id,
                            conversations=convs_resp,
                            **profile.__dict__)
