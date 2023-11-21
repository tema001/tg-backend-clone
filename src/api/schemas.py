from datetime import datetime

from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

from shared import idType


class ConversationResponse(BaseModel):
    id: str
    type: str
    name: str | None
    created_at: datetime
    participants: list[dict]
    creator_id: str | None

    def __init__(self, user_id: str, data):
        super().__init__(id=str(data.get('_id')), **data)
        if self.type == 'private':
            self.participants[:] = [
                x for x in self.participants if str(x.get('_id')) != user_id
            ]
            self.name = self.participants[0].get('name')

        self.participants[:] = [
            jsonable_encoder(x, exclude_none=True, custom_encoder={idType: str})
            for x in self.participants
        ]


class UserInfoResponse(BaseModel):
    id: str
    username: str
    name: str
    conversations: list[ConversationResponse]
