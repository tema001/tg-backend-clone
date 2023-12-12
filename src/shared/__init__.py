import json
import os
from uuid import uuid4
from dataclasses import dataclass
from typing import Dict

from bson import ObjectId

idType = ObjectId

file_type_map = {'binaryFile': 'File', 'audioFile': 'Audio'}

TEMP_STORAGE = '/tmp/storage/'
if not os.path.exists(TEMP_STORAGE):
    os.mkdir(TEMP_STORAGE)


class TempInnerStorageWriter:

    def __init__(self, blob: bytes):
        temp_dir = str(uuid4())
        self._path = TEMP_STORAGE + temp_dir
        os.mkdir(self._path)

        self.file = BinaryFile(blob, temp_dir)

    def __enter__(self):
        self._data_size = 0
        self._fd = open(self._path + '/' + self.file.filename, 'x+b')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fd.close()

    async def write(self, data: bytes) -> bool:
        self._fd.write(data)

        self._data_size += len(data)
        return self._data_size >= self.file.total_size


class TempStorage:
    @staticmethod
    def is_new_file(blob: bytes) -> bool:
        return blob[0:3] == b'!_!'

    @staticmethod
    def full_path(temp_dir: str, filename: str) -> str:
        return TEMP_STORAGE + temp_dir + '/' + filename

    @staticmethod
    def init_writer(blob: bytes) -> TempInnerStorageWriter:
        return TempInnerStorageWriter(blob)


@dataclass(slots=True, init=False)
class BinaryFile:
    filename: str
    total_size: int
    type: str
    metadata: Dict
    temp_dir: str

    def __init__(self, blob: bytes, temp_dir: str):
        header = json.loads(blob[3:])
        self.filename = header.pop('name')
        self.total_size = int(header.pop('size'))
        self.type = file_type_map.get(header.pop('type'))
        self.metadata = header
        self.temp_dir = temp_dir
