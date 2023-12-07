import json
import socket
import time

from wsproto import WSConnection
from wsproto.connection import ConnectionType
from wsproto.events import (
    AcceptConnection,
    CloseConnection,
    Message,
    Request,
    TextMessage,
)

RECEIVE_BYTES = 4096
MESSAGE_COUNT = 200


def wsproto_demo(username: str, profile_id: str, conv_id: str, results: list) -> None:
    host = 'localhost'
    port = 8010

    # print(f"Connecting to {host}:{port}")
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, port))

    # 1) Negotiate WebSocket opening handshake
    ws = WSConnection(ConnectionType.CLIENT)
    # Because this is a client WebSocket, we need to initiate the connection
    # handshake by sending a Request event.
    net_send(ws.send(Request(host=host, target=profile_id)), conn)
    net_recv(ws, conn)
    handle_events(ws)

    start = time.time()
    for x in range(MESSAGE_COUNT):
        # 2) Send a message and display response
        msg = {'conversation_id': conv_id, 'type': 'Text', 'payload': 'awiwa'}

        try:
            net_send(ws.send(Message(data=json.dumps(msg))), conn)

            net_recv(ws, conn)
        except BrokenPipeError as e:
            print(f'Cannot send message #{x} by user {username}')

        handle_events(ws)

    finish = time.time()
    results.append((username, finish - start))

    # 3) Negotiate WebSocket closing handshake
    # print("Closing WebSocket")
    net_send(ws.send(CloseConnection(code=1000, reason="sample reason")), conn)
    net_recv(ws, conn)
    conn.shutdown(socket.SHUT_WR)
    net_recv(ws, conn)


def net_send(out_data: bytes, conn: socket.socket) -> None:
    # print("Sending {} bytes".format(len(out_data)))
    conn.send(out_data)


def net_recv(ws: WSConnection, conn: socket.socket) -> None:
    in_data = conn.recv(RECEIVE_BYTES)
    if not in_data:
        # A receive of zero bytes indicates the TCP socket has been closed. We
        # need to pass None to wsproto to update its internal state.
        ws.receive_data(None)
    else:
        # print("Received {} bytes".format(len(in_data)))
        ws.receive_data(in_data)


def handle_events(ws: WSConnection) -> None:
    for event in ws.events():
        if isinstance(event, AcceptConnection):
            # print("WebSocket negotiation complete")
            pass
        elif isinstance(event, TextMessage):
            msg = json.loads(event.data)
            # print(f"Received message: {msg['status']}")
        else:
            raise Exception("Do not know how to handle event: " + str(event))

