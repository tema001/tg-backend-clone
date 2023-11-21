from fastapi import Depends

from pymongo import ASCENDING, DESCENDING
from pymongo.database import Collection

from db import get_messages
from bson import ObjectId


class MessageRepository:

    def __init__(self, db: Collection = Depends(get_messages)):
        self._db = db

    def get_by_id(self, _id: ObjectId):
        return self._db.find_one({'_id': _id})

    def add(self, message: dict) -> ObjectId:
        msg_id = self._db.insert_one(message)
        return msg_id.inserted_id

    def get_by_conversation_id(self, _id: ObjectId):
        return self._db.find({'conversation_id': _id}).limit(40).sort('created_at', DESCENDING)

    def set_seen_status(self, _id: ObjectId, event: dict) -> bool:
        res = self._db.update_one(
            {'_id': _id},
            {
              '$set': {'status': 'Seen'},
              '$push': {'events': event}
            }
        )
        return res.matched_count == 1
