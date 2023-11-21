from fastapi import Depends
from pymongo.database import Collection

from db import get_profiles
from profile.domain.entity import ProfileEntity
from shared import idType


# PROFILES
# {
#     _id: ObjectId("65341fd14aae74d5e1c08f78"),
#     username: 'artem',
#     password: '123',
#     name: '3232'
#     contacts: [1,2,3,],
#     created_at: ISODate("2023-10-21T18:49:06.273Z"),
# }


class ProfileRepository:

    def __init__(self, db: Collection = Depends(get_profiles)):
        self._db = db

    def add(self, profile: ProfileEntity):
        self._db.insert_one(profile.__dict__)

    def get_by_id(self, _id: idType) -> ProfileEntity:
        profile = self._db.find_one({'_id': _id})
        return ProfileEntity(**profile)

    def get_by_username(self, username: str) -> ProfileEntity | None:
        profile = self._db.find_one({'username': username})
        if profile:
            return ProfileEntity(**profile)
