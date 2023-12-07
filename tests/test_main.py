import os

from statistics import mean
from threading import Thread
from typing import List, Dict
from httpx import Client

from ws_test_client import wsproto_demo

USER_PATTERN = 'test_user_'


def _load_users(array: List, file_name: str) -> bool:
    if not os.path.exists(file_name):
        return False

    with open(file_name, 'rt') as file:
        _ = file.readline()
        for row in file:
            name, _id = row.split(';')
            array.append((name, _id.rstrip('\n')))

    return True


def _save_users(array: List, file_name: str):
    with open(file_name, 'xt') as file:
        file.write('username;id\n')
        for x in array:
            file.write(x[0] + ';' + x[1] + '\n')


def test_register(req: Client, users_range: tuple, file_name: str, users: List):
    if _load_users(users, file_name):
        return

    offset, limit = users_range

    for x in range(offset, limit + 1):
        uname = USER_PATTERN + str(x)
        body = {
            "username": uname,
            "password": "123"
        }
        resp = req.post('/register', json=body)
        if resp.is_success:
            print(resp.text)
            users.append((uname, resp.text.strip('"')))
        else:
            print(resp.status_code)
            print(resp.reason_phrase)

    _save_users(users, file_name)


def get_token(req, user: tuple, users_data: Dict):
    body = {
        "username": user[0],
        "password": "123"
    }
    resp = req.post('/token', data=body)
    if resp.is_success:
        token = resp.json()
        users_data[user] = (f"{token['token_type']} {token['access_token']}", )
        return resp.elapsed.total_seconds()
    else:
        print(resp.status_code, resp.reason_phrase)


def test_get_tokens(req: Client, users: List, users_data: Dict, pool):
    args = ((req, user, users_data) for user in users)
    elapsed_time = pool.starmap(get_token, args)
    print(elapsed_time)
    print(mean(elapsed_time))


def start_conversation(req, prev_user: tuple, user: tuple, users_data: Dict):
    _token = users_data[user][0]
    headers = {'Authorization': _token}
    resp = req.post(f'/contact/{prev_user[1]}/chat', headers=headers)
    if resp.is_success:
        users_data[user] = (_token, resp.text.strip('"'))
        return resp.elapsed.total_seconds()
    else:
        print(resp.status_code)
        print(resp.reason_phrase)


def test_start_conversation(req: Client, users: List, users_data: Dict, pool):
    args = ((req, f, s, users_data) for f, s in zip(users, users[::-1]))
    elapsed_time = pool.starmap(start_conversation, args)
    print(elapsed_time)
    print(mean(elapsed_time))


def test_ws_messaging(users_data: Dict):
    threads = []
    results = []
    for user, data in users_data.items():
        thread = Thread(target=wsproto_demo, args=(*user, data[1], results), daemon=True)
        thread.start()
        threads.append(thread)

    for x in threads:
        x.join()

    print(results)
    print(mean((res[1] for res in results)))
