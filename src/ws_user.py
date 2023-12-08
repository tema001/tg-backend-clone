import asyncio
import socket
import time

from starlette.concurrency import run_in_threadpool

from wsproto import ConnectionType, WSConnection
from wsproto.events import (
    AcceptConnection,
    RejectConnection,
    CloseConnection,
    Message,
    Ping,
    Request,
    TextMessage,
    BytesMessage
)

from shared import idType, BinaryFile
from profile.application import ProfileService
from task_manager.domain.manager import TaskManager
from task_manager.domain.tasks import TaskFactory


class WebSocketUser:
    RECEIVE_BYTES = 1024 * 2

    def __init__(self, stream: socket.socket, task_manager: TaskManager):
        self.tm = task_manager
        self.stream = stream
        self.loop = asyncio.get_event_loop()
        self._id = None
        self._running = False

    async def _ws_handshake(self) -> WSConnection | None:
        ws = WSConnection(ConnectionType.SERVER)

        in_data = await self.loop.sock_recv(self.stream, self.RECEIVE_BYTES)
        ws.receive_data(in_data)
        event = next(ws.events())

        if isinstance(event, Request):
            print("Accepting WebSocket upgrade")
            if event.target.startswith('/ws?'):
                self._id = await self._authorize(event.target)
            else:
                _id = event.target[event.target.rfind('/') + 1:]
                self._id = idType(_id)
            if self._id:
                await self.loop.sock_sendall(self.stream, ws.send(AcceptConnection()))
                return ws

        await self.loop.sock_sendall(self.stream, ws.send(RejectConnection()))

    @staticmethod
    async def _authorize(path: str) -> idType | None:
        if 'Authorization=' in path:
            _, token = path.split('Authorization=')
            try:
                user = await ProfileService.get_user_from_token(token)
                return idType(user['id'])
            except Exception as e:
                print(e.args)

    async def run(self):
        try:
            if ws := await self._ws_handshake():
                self.ws = ws
                self._running = True
                self.tm.new_connection(self._id, self.push_msg)
                await self.handle_incoming_msg()
        except Exception as e:
            print(e)
            self.stream.shutdown(socket.SHUT_WR)
            raise e
        finally:
            self.stream.close()

    async def handle_incoming_msg(self) -> None:
        _file = None

        while self._running:
            in_data = await self.loop.sock_recv(self.stream, WebSocketUser.RECEIVE_BYTES)
            await run_in_threadpool(self.ws.receive_data, in_data)

            for event in self.ws.events():

                if isinstance(event, CloseConnection):
                    self._running = False

                    self.tm.close_connection(self._id)
                    out_data = self.ws.send(event.response())
                    await self.loop.sock_sendall(self.stream, out_data)

                elif isinstance(event, TextMessage):
                    task = await run_in_threadpool(TaskFactory.create_task, self._id, event.data)
                    await self.tm.add_task(task)

                elif isinstance(event, BytesMessage):
                    if BinaryFile.is_new_file(event.data):
                        _file = BinaryFile(event.data)
                    else:
                        if _file.load(event.data):
                            task = await run_in_threadpool(TaskFactory.create_task, self._id, _file)
                            await self.tm.add_task(task)
                            _file = None

                elif isinstance(event, Ping):
                    out_data = self.ws.send(event.response())
                    await self.loop.sock_sendall(self.stream, out_data)

                else:
                    print(f"Unknown event: {event!r}")

    async def push_msg(self, payload: str):
        if self._running:
            await self.loop.sock_sendall(self.stream, self.ws.send(Message(payload)))

