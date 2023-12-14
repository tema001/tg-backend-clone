from statistics import mean

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException, status

from shared import idType
from shared.utils import GridFsStorage
from task_manager.domain.manager import TaskManager

from ws_user import WebSocketUser

router = APIRouter()
tm = TaskManager()
storage = GridFsStorage()


@router.websocket('/ws')
# @router.websocket('/ws/{user_id}')
async def ws_user(websocket: WebSocket,
                  # user_id: str,
                  ):
    token = websocket.query_params.get('Authorization')
    user_id = await WebSocketUser.authorize(token)

    if user_id is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user_id = idType(user_id)
    await websocket.accept()

    user = WebSocketUser(tm, user_id, storage, websocket.send_text)

    try:
        await user.handle_incoming_msg(websocket.receive)
    except WebSocketDisconnect:
        ...
