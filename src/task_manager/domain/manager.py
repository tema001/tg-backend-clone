import json
import time
from typing import Callable, Iterable, Dict, List

from queue import Queue

from conversations.domain.entity import ConversationEntity
from conversations.repository import ConversationRepository
from messages.repository import MessageRepository

from shared import idType
from shared.utils import FileStorage
from .tasks import Task, SendMsg, LoadAllMsgs
from .di import di_cache


class TaskManager:
    _instance = None

    _chat_cache: dict[idType, ConversationEntity] = {}

    _connected_users: dict[idType, Callable] = {}

    _task_queue: Queue = Queue()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self,
                 conv_repo: ConversationRepository,
                 messages_repo: MessageRepository,
                 file_storage):
        self._running = True
        self.conv_repo = conv_repo

        di_cache[ConversationRepository] = self.conv_repo
        di_cache[MessageRepository] = messages_repo
        di_cache[Callable[[idType], ConversationEntity]] = self._get_conversation
        di_cache[FileStorage] = file_storage

    def main_loop(self):
        while self._running:
            for _ in range(self._task_queue.qsize()):
                self._handle_message(self._task_queue.get_nowait())
            time.sleep(0.1)

    def _handle_message(self, task: Task):
        result = task.handle()

        self._messages_dispatch(result.receiver, result.payload)

    def _messages_dispatch(self, receiver: idType | Iterable, msg: Dict):
        def _send(_id):
            receiver_func = self._connected_users.get(_id)
            if receiver_func:
                receiver_func(json.dumps(msg, default=str))

        if isinstance(receiver, Iterable):
            for x in receiver:
                _send(x)
        else:
            _send(receiver)

    def _get_conversation(self, conv_id: idType) -> ConversationEntity | None:
        conversation = self._chat_cache.get(conv_id)
        if not conversation:
            conversation = self.conv_repo.get_by_id(conv_id)
            if conversation:
                self._chat_cache[conv_id] = conversation

        return conversation

    def add_task(self, new_task: Task):
        self._task_queue.put(new_task)

    def new_connection(self, client_id: idType, callback: Callable):
        print(f'New connection: {client_id}')

        self._connected_users[client_id] = callback

        self._task_queue.put(LoadAllMsgs(client_id))

    def close_connection(self, client_id: idType):
        print(f'Closing connection: {client_id}')
        if self._connected_users.get(client_id):
            del self._connected_users[client_id]

    def shutdown(self):
        self._running = False

