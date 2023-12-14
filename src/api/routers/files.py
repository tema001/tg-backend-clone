from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse

from messages.repository import MessageRepository

from shared import idType
from shared.utils import GridFsStorage

router = APIRouter(prefix='/f')


@router.get('/{message_id}')
def get_file(message_id: str,
             msg_repo: MessageRepository = Depends(),
             file_storage: GridFsStorage = Depends()):
    msg = msg_repo.get_by_id(idType(message_id))
    msg_payload = msg['payload']

    stream = file_storage.load_stream(idType(msg_payload['file_id']))
    if not stream:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail='File not exist')

    filename = msg_payload['filename']
    header = {'Content-Disposition': f'attachment; filename="{filename}"'}
    return StreamingResponse(content=stream, headers=header)
