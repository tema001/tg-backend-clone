import asyncio
import socket

from task_manager.domain.manager import TaskManager
from ws_user import WebSocketUser


class SimpleWebSocketServer:
    IP = 'localhost'
    PORT = 8010

    def __init__(self, task_manager: TaskManager):
        self.tm = task_manager
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    async def main(self) -> None:
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.IP, self.PORT))
        self.server.listen()

        loop = asyncio.get_event_loop()

        try:
            while True:
                print("Waiting for connection...")
                stream, addr = await loop.sock_accept(self.server)
                user = WebSocketUser(stream, self.tm)
                asyncio.create_task(user.run())
        except KeyboardInterrupt:
            print('Received SIGINT: shutting down')
        except ConnectionAbortedError:
            print('Received ConnectionAborted: shutting down')

    def shutdown(self):
        # self.server.shutdown(socket.SHUT_WR)
        self.server.close()
