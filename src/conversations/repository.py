from fastapi import Depends
from pymongo.database import Collection
from starlette.concurrency import run_in_threadpool

from conversations.domain.entity import ConversationEntity
from db import get_conversations

from bson import ObjectId


class ConversationRepository:

    def __init__(self, db: Collection = Depends(get_conversations)):
        self._db = db

    async def add(self, conversation: ConversationEntity):
        await run_in_threadpool(self._db.insert_one, conversation.__dict__)

    async def get_by_id(self, _id: ObjectId) -> ConversationEntity | None:
        resp = await run_in_threadpool(self._db.find_one, {'_id': _id})
        if resp:
            return ConversationEntity(**resp)

    async def find_private_by_ids(self,
                            _id_1: ObjectId,
                            _id_2: ObjectId) -> ConversationEntity | None:
        _filter = {
            'type': 'private',
            'participants': {'$size': 2, '$all': [_id_1, _id_2]}
        }
        resp = await run_in_threadpool(self._db.find_one, _filter)
        if resp:
            return ConversationEntity(**resp)

    def find_all_by_participant_id(self, _id: ObjectId):
        return self._db.find({'participants': _id}, {'_id': 1})

    def find_all_detailed_by_participant_id(self, _id: ObjectId):
        pipeline = [
            {'$match':
                 {'participants': _id}
            },
            {'$lookup':
                {'from': "Profiles",
                 'localField': "participants",
                 'foreignField': "_id",
                 'pipeline': [{'$project': {'name': 1, 'username': 1}}],
                 'as': "participants"}
             }]
        resp = self._db.aggregate(pipeline)

        return resp
