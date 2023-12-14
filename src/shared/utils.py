import os.path
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Generator

from gridfs import NoFile

from . import idType, BinaryFile
from db import bucket


class FileStorage(ABC):

    @abstractmethod
    def save(self, *args):
        ...

    @abstractmethod
    def load(self, *args):
        ...


class FileStorageStream(ABC):

    @abstractmethod
    def save_stream(self, *args):
        ...

    @abstractmethod
    def load_stream(self, *args):
        ...

    @abstractmethod
    def remove(self, *args):
        ...


class GridFsWriter:

    def __init__(self, _id, file_size: int, filename: str):
        self._data_size = 0
        self.file_size = file_size
        self._fw = bucket.open_upload_stream_with_id(_id, filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fw.close()

    def write(self, data: bytes) -> bool:
        self._fw.write(data)

        self._data_size += len(data)
        return self._data_size >= self.file_size


class GridFsStorage(FileStorageStream):

    @classmethod
    def save_stream(cls, b_file: BinaryFile) -> GridFsWriter:
        b_file.file_id = idType()
        return GridFsWriter(b_file.file_id, b_file.total_size, b_file.filename)

    @staticmethod
    def load_stream(_id: idType) -> Generator | None:
        try:
            with bucket.open_download_stream(_id) as grid_out:
                while batch := grid_out.readchunk():
                    yield batch
        except NoFile:
            return None

    @staticmethod
    def remove(_id: idType):
        bucket.delete(_id)
