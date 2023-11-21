from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from messages.repository import MessageRepository

from shared import idType
from shared.utils import DummyFileStorage

router = APIRouter(prefix='/f')


@router.get('/{message_id}')
def get_file(message_id: str,
             msg_repo: MessageRepository = Depends(),
             file_storage: DummyFileStorage = Depends()):
    msg = msg_repo.get_by_id(idType(message_id))
    filename = msg['payload']['filename']

    stream = file_storage.load_stream(msg['conversation_id'], filename)
    if not stream:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='File not exist')

    header = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(content=stream, headers=header)
