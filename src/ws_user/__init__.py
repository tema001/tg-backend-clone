import asyncio
import time
from statistics import mean
from typing import Awaitable, Callable

from starlette.concurrency import run_in_threadpool
from websockets.exceptions import ConnectionClosedOK

from shared import idType, BinaryFile
from profile.application import ProfileService
from shared.utils import FileStorageStream
from task_manager.domain.manager import TaskManager
from task_manager.domain.tasks import TaskFactory


class WebSocketUser:
    def __init__(self,
                 task_manager: TaskManager,
                 user_id: idType,
                 storage: FileStorageStream,
                 writer):
        self.tm = task_manager
        self._id = user_id
        self._writer = writer
        self._storage = storage
        self._running = True
        self.aaa = []

        self.tm.new_connection(self._id, self.push_msg)

    @staticmethod
    async def authorize(token: str) -> idType | None:
        try:
            user = await ProfileService.get_user_from_token(token)
            return idType(user['id'])
        except Exception as e:
            print(e.args)

    async def handle_incoming_msg(self, reader: Callable[..., Awaitable[dict]]) -> None:

        while self._running:
            data = await reader()
            event = data['type']
            if event == 'websocket.disconnect':
                self._running = False
                self.tm.close_connection(self._id)

            elif event == 'websocket.receive':
                if 'text' in data:
                    task = await run_in_threadpool(TaskFactory.create_task, self._id, data['text'])
                    self.tm.add_task(task)
                else:
                    b_data = data['bytes']
                    if BinaryFile.is_new_file(b_data):
                        await self._load_file(b_data, reader)
            else:
                print(f"Unknown event: {event!r}")

    async def _load_file(self, b_data, reader):
        completed = False

        b_file = BinaryFile(b_data)
        with self._storage.save_stream(b_file) as fw:
            print('Start loading the file')
            try:
                while not completed:
                    data = await asyncio.wait_for(reader(), timeout=3.0)
                    completed = fw.write(data['bytes'])
            except TimeoutError:
                print('WS file reading time out!')
            except Exception as e:
                print('Unexpected exception during loading')
                print(e.args)

        if completed:
            print('File is successfully loaded and saved!')
            task = await run_in_threadpool(TaskFactory.create_task, self._id, b_file)
            self.tm.add_task(task)
        else:
            self._storage.remove(b_file.file_id)
            b_file = None
            # todo

    async def push_msg(self, payload: str):
        if self._running:
            try:
                await self._writer(payload)
            except ConnectionClosedOK:
                print('closedddddddddddd')
