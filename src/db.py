from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['messanger_db']

messages      = db['Messages']
conversations = db['Conversations']
profiles      = db['Profiles']


def get_conversations():
    return conversations


def get_profiles():
    return profiles


def get_messages():
    return messages
