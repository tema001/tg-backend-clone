import json
from dataclasses import dataclass
from typing import Dict

from bson import ObjectId

idType = ObjectId

file_type_map = {'binaryFile': 'File', 'audioFile': 'Audio'}


@dataclass(slots=True, init=False)
class BinaryFile:
    filename: str
    total_size: int
    type: str
    metadata: Dict
    file_id: idType

    def __init__(self, blob: bytes):
        header = json.loads(blob[3:])
        self.filename = header.pop('name')
        self.total_size = int(header.pop('size'))
        self.type = file_type_map.get(header.pop('type'))
        self.metadata = header

    @staticmethod
    def is_new_file(blob: bytes) -> bool:
        return blob[0:3] == b'!_!'
