from dataclasses import dataclass, field
from datetime import datetime

from ..application.utils import hash_password

from shared import idType
from typing import List


@dataclass
class ProfileEntity:
    _id: idType
    username: str
    password: str
    name: str
    contacts: List = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, username: str, password: str):
        return cls(_id=idType(),
                   username=username,
                   password=hash_password(password),
                   name=username
        )