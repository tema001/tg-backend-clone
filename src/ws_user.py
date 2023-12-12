import asyncio
import time
from typing import Awaitable, Callable

from starlette.concurrency import run_in_threadpool
from websockets.exceptions import ConnectionClosedOK

from shared import idType, TempStorage
from profile.application import ProfileService
from task_manager.domain.manager import TaskManager
from task_manager.domain.tasks import TaskFactory


class WebSocketUser:
    def __init__(self, task_manager: TaskManager, user_id: idType, writer):
        self.tm = task_manager
        self._id = user_id
        self._writer = writer
        self._running = True

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
                    await self.tm.add_task(task)
                else:
                    b_data = data['bytes']
                    if TempStorage.is_new_file(b_data):
                        await self.__load_file(b_data, reader)
            else:
                print(f"Unknown event: {event!r}")

    async def __load_file(self, b_data, reader):
        completed = False

        with TempStorage.init_writer(b_data) as fw:
            try:
                while not completed:
                    data = await asyncio.wait_for(reader(), timeout=5.0)
                    completed = await fw.write(data['bytes'])
            except TimeoutError:
                print('WS file reading time out!')
            except Exception as e:
                print('Unexpected exception during loading')
                print(e.args)

        if completed:
            task = await run_in_threadpool(TaskFactory.create_task, self._id, fw.file)
            await self.tm.add_task(task)
        else:
            # todo
            ...

    async def push_msg(self, payload: str):
        if self._running:
            try:
                await self._writer(payload)
            except ConnectionClosedOK:
                print('closedddddddddddd')
