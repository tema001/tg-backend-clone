import json
import asyncio
import time
from typing import Callable, Iterable, Dict, Awaitable

from conversations.domain.entity import ConversationEntity
from conversations.repository import ConversationRepository
from messages.repository import MessageRepository

from shared import idType
from shared.utils import FileStorage
from .tasks import Task, LoadAllMsgs
from .di import di_cache


class TaskManager:
    _instance = None

    _chat_cache: dict[idType, ConversationEntity] = {}

    _connected_users: dict[idType, Callable] = {}

    _task_queue: asyncio.Queue = asyncio.Queue()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self,
                 conv_repo: ConversationRepository = None,
                 messages_repo: MessageRepository = None,
                 file_storage = None):
        self._running = True
        self.conv_repo = conv_repo

        self.get_task = []

        di_cache[ConversationRepository] = self.conv_repo
        di_cache[MessageRepository] = messages_repo
        di_cache[Callable[[idType], Awaitable[ConversationEntity]]] = self._get_conversation
        di_cache[FileStorage] = file_storage

    async def main_loop(self):
        count = 0
        while self._running:
            try:
                start = time.time()
                task = await self._task_queue.get()
                await self._handle_message(task)
                finish = time.time()
                self.get_task.append(finish - start)

                count += 1
                if count > 500:
                    await asyncio.sleep(0.01)
                    count = 0
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)

    async def _handle_message(self, task: Task):
        result = await task.handle()
        self._task_queue.task_done()

        await self._messages_dispatch(result.receiver, result.payload)

    async def _messages_dispatch(self, receiver: idType | Iterable, msg: Dict):
        async def _send(_id):
            receiver_func = self._connected_users.get(_id)
            if receiver_func:
                await receiver_func(json.dumps(msg, default=str))

        if isinstance(receiver, Iterable):
            for x in receiver:
                await _send(x)
        else:
            await _send(receiver)

    async def _get_conversation(self, conv_id: idType) -> ConversationEntity | None:
        conversation = self._chat_cache.get(conv_id)
        if not conversation:
            conversation = await self.conv_repo.get_by_id(conv_id)
            if conversation:
                self._chat_cache[conv_id] = conversation

        return conversation

    async def add_task(self, new_task: Task):
        await self._task_queue.put(new_task)
        await asyncio.sleep(0)

    def new_connection(self, client_id: idType, callback: Callable):
        print(f'New connection: {client_id}')

        self._connected_users[client_id] = callback

        # self._task_queue.put(LoadAllMsgs(client_id))

    def close_connection(self, client_id: idType):
        print(f'Closing connection: {client_id}')
        if self._connected_users.get(client_id):
            del self._connected_users[client_id]

    def shutdown(self):
        self._running = False
