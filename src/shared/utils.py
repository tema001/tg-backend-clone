import os.path
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Generator


class FileStorage(ABC):

    @abstractmethod
    async def save(self, *args):
        ...

    @abstractmethod
    def load_stream(self, *args):
        ...


class DummyFileStorage(FileStorage):
    def __init__(self):
        self._storage_path = '/Users/artem/Documents/storage/'

    async def save(self, fd: BytesIO, sub_dir: str, name: str):
        # imitation of transfer from ws server to a file service
        sub_path = self._storage_path + sub_dir
        if not os.path.exists(sub_path):
            os.mkdir(sub_path)

        with open(f'{sub_path}/{name}', 'wb') as file:
            while batch := fd.read(1024):
                file.write(batch)

    def load_stream(self, sub_dir: str, name: str) -> Generator | None:
        file_path = f'{self._storage_path}{sub_dir}/{name}'

        if not os.path.exists(file_path):
            return None

        with open(file_path, 'rb') as file:
            batch_s = 1024
            while batch := file.read(batch_s):
                yield batch
