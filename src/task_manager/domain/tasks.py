import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Callable, Iterable, Any, Awaitable

import ujson

from conversations.domain.entity import ConversationEntity
from conversations.repository import ConversationRepository
from messages.repository import MessageRepository
from shared import idType, BinaryFile, TempStorage
from shared.utils import FileStorage

from .di import inject


@dataclass(slots=True, frozen=True, eq=False)
class TaskResult:
    receiver: idType | Iterable
    payload: Dict


class Task(ABC):

    @abstractmethod
    async def handle(self, *args) -> TaskResult:
        raise NotImplementedError


class TaskFactory:

    @classmethod
    def create_task(cls, sender_id: idType, data: Any) -> Task:
        new_task = None
        if isinstance(data, str):
            _data = ujson.loads(data)
            data_type = _data.get('type')
            if data_type == 'Text':
                new_task = SendMsg.create(sender_id, _data)
            elif data_type == 'ReadMsg':
                new_task = ReadMsgEvent.create(sender_id, _data)

        elif isinstance(data, BinaryFile):
            new_task = DownloadFile.create(sender_id, data)

        if new_task is None:
            print('*** Task factory cannot define a task ***')

        return new_task


@dataclass(slots=True, frozen=True)
class ReadMsgEvent(Task):
    sender_id: idType
    conversation_id: idType
    message_id: idType
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, sender_id: idType, data: str | Dict):
        if isinstance(data, str):
            data = json.loads(data)
        return cls(sender_id, idType(data['conversation_id']), idType(data['message_id']))

    @inject
    def handle(self,
               msg_repo: MessageRepository,
               get_conv: Callable[[idType], ConversationEntity]
               ) -> TaskResult:

        conv = get_conv(self.conversation_id)
        if conv is None:
            msg = {'type': 'Error', 'description': 'No such conversation'}
            return TaskResult(self.sender_id, msg)

        msg = {'type': 'SeenMsg', 'created_at': self.created_at}
        resp = msg_repo.set_seen_status(self.message_id, msg)
        if not resp:
            msg = {'type': 'Error', 'description': 'Cannot modify status'}
            return TaskResult(self.sender_id, msg)

        msg['message_id'] = self.message_id
        msg['conversation_id'] = self.conversation_id

        return TaskResult(conv.participants, msg)


@dataclass(slots=True, frozen=True)
class SendMsg(Task):
    sender_id: idType
    conversation_id: idType
    payload: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, sender_id: idType, data: str | Dict):
        if isinstance(data, str):
            data = json.loads(data)
        return cls(sender_id, idType(data['conversation_id']), data['payload'])

    @inject
    async def handle(self,
                     msg_repo: MessageRepository,
                     get_conv: Callable[[idType], Awaitable[ConversationEntity]]
                     ) -> TaskResult:
        conv = await get_conv(self.conversation_id)

        if conv is None:
            msg = {'type': 'Error', 'description': 'No such conversation'}
            return TaskResult(self.sender_id, msg)

        msg = {
            'sender_id': self.sender_id,
            'conversation_id': self.conversation_id,
            'type': 'Text',
            'status': 'Sent',
            'payload': self.payload,
            'created_at': self.created_at,
            'events': []
        }
        msg_id = await msg_repo.add(msg)
        msg['_id'] = msg_id

        return TaskResult(conv.participants, msg)


@dataclass(slots=True, frozen=True)
class DownloadFile(Task):
    sender_id: idType
    conversation_id: idType
    payload: BinaryFile
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(cls, sender_id: idType, data: BinaryFile):
        return cls(sender_id, idType(data.metadata['conversation_id']), data)

    @inject
    async def handle(self,
                     msg_repo: MessageRepository,
                     file_storage: FileStorage,
                     get_conv: Callable[[idType], Awaitable[ConversationEntity]]
                     ) -> TaskResult:
        conv = await get_conv(self.conversation_id)

        if conv is None:
            msg = {'type': 'Error', 'description': 'No such conversation'}
            return TaskResult(self.sender_id, msg)

        msg = {
            'sender_id': self.sender_id,
            'conversation_id': self.conversation_id,
            'type': self.payload.type,
            'status': 'Sent',
            'payload': {
                'size': self.payload.total_size,
                'filename': self.payload.filename
            },
            'created_at': self.created_at,
            'events': []
        }
        msg_id = await msg_repo.add(msg)
        msg['_id'] = msg_id

        # todo: try/except
        path = TempStorage.full_path(self.payload.temp_dir, self.payload.filename)
        with open(path, 'rb') as fd:
            await file_storage.save(fd, str(self.conversation_id), self.payload.filename)

        return TaskResult(conv.participants, msg)


@dataclass(slots=True, frozen=True)
class LoadAllMsgs(Task):
    requester_id: idType

    @inject
    async def handle(self,
                     conv_repo: ConversationRepository,
                     msg_repo: MessageRepository,
                     ) -> TaskResult:
        chats = await conv_repo.find_all_by_participant_id(self.requester_id)
        payload = {'type': 'AllMessages'}
        for chat in chats:
            m = list(await msg_repo.get_by_conversation_id(chat['_id']))
            m.reverse()
            _id = str(chat['_id'])
            payload[_id] = m

        return TaskResult(self.requester_id, payload)
