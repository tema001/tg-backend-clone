from multiprocessing.pool import ThreadPool

from pytest import fixture
import httpx

POOL_SIZE = 20


@fixture(scope='session')
def users():
    return []


@fixture(scope='session')
def users_data():
    return {}


@fixture(scope='session')
def file_name():
    return './storage.csv'


@fixture(scope='session')
def users_range():
    # the total number of users must be even
    return 1, 100


@fixture(scope='session')
def req():
    with httpx.Client(base_url='http://localhost:8000') as req:
        yield req


@fixture(scope='session')
def pool():
    with ThreadPool(POOL_SIZE) as pool:
        yield pool
