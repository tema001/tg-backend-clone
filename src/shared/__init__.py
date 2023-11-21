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
    data: bytes = b''

    def __init__(self, blob: bytes):
        header_b, self.data = blob.split(b'\r\n\r\n')
        header = json.loads(header_b[3:])
        self.filename = header.pop('name')
        self.total_size = int(header.pop('size'))
        self.type = file_type_map.get(header.pop('type'))
        self.metadata = header

    def load(self, more_data: bytes) -> bool:
        self.data += more_data
        if len(self.data) >= self.total_size:
            return True

        return False

    @staticmethod
    def is_new_file(blob: bytes) -> bool:
        return blob[0:3] == b'!_!'


