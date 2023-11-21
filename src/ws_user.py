import socket

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
        self._id = None
        if ws := self._ws_handshake(stream):
            self.tm = task_manager
            self.ws = ws
            self.stream = stream
            self._running = True
            self.tm.new_connection(self._id, self.push_msg)
            self._run()
        else:
            stream.shutdown(socket.SHUT_WR)
            stream.close()

    def _ws_handshake(self, stream: socket.socket) -> WSConnection | None:
        ws = WSConnection(ConnectionType.SERVER)

        in_data = stream.recv(self.RECEIVE_BYTES)
        ws.receive_data(in_data)
        event = next(ws.events())

        if isinstance(event, Request):
            print("Accepting WebSocket upgrade")
            self._id = self._authorize(event.target)
            if self._id:
                stream.send(ws.send(AcceptConnection()))
                return ws

        stream.send(ws.send(RejectConnection()))

    @staticmethod
    def _authorize(path: str) -> idType | None:
        if 'Authorization=' in path:
            _, token = path.split('Authorization=')
            try:
                user = ProfileService.get_user_from_token(token)
                return idType(user['id'])
            except Exception as e:
                print(e.args)

    def _run(self):
        try:
            self.handle_incoming_msg()
        except Exception as e:
            print(e)
            self.stream.shutdown(socket.SHUT_WR)
            raise e
        finally:
            self.stream.close()

    def handle_incoming_msg(self) -> None:
        _file = None

        while self._running:
            in_data = self.stream.recv(WebSocketUser.RECEIVE_BYTES)
            self.ws.receive_data(in_data)

            for event in self.ws.events():
                if isinstance(event, CloseConnection):
                    self.tm.close_connection(self._id)
                    out_data = self.ws.send(event.response())
                    self.stream.send(out_data)

                    self._running = False
                elif isinstance(event, TextMessage):
                    print("Received request")
                    self.tm.add_task(
                        TaskFactory.create_task(self._id, event.data)
                    )
                elif isinstance(event, BytesMessage):
                    if BinaryFile.is_new_file(event.data):
                        _file = BinaryFile(event.data)
                    else:
                        if _file.load(event.data):
                            self.tm.add_task(
                                TaskFactory.create_task(self._id, _file)
                            )
                            _file = None
                elif isinstance(event, Ping):
                    out_data = self.ws.send(event.response())
                    self.stream.send(out_data)
                else:
                    print(f"Unknown event: {event!r}")

    def push_msg(self, payload: str):
        if self._running:
            self.stream.send(self.ws.send(Message(payload)))

