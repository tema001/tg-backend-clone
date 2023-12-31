from pymongo import MongoClient
import gridfs

client = MongoClient('localhost', 27017)
db = client['messanger_db']

messages      = db['Messages']
conversations = db['Conversations']
profiles      = db['Profiles']

f_db = client['files_db']
bucket = gridfs.GridFSBucket(f_db)


def get_conversations():
    return conversations


def get_profiles():
    return profiles


def get_messages():
    return messages
