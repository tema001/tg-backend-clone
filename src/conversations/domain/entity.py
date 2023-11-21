from dataclasses import dataclass
from typing import Iterable
from datetime import datetime

from shared import idType


@dataclass
class ConversationEntity:
    _id: idType
    type: str
    name: str | None
    created_at: datetime
    participants: Iterable[idType]
    creator_id: idType | None = None

    @classmethod
    def create(cls, type: str, participants: Iterable, name: str = None, creator_id: idType = None):
        return cls(_id=idType(),
                   type=type,
                   name=name,
                   participants=participants,
                   creator_id=creator_id,
                   created_at=datetime.utcnow())

