# Functions for keeping track of user data

import redis
import json
import sys
from backend.settings import REDIS_QUEUE_LENGTH
from backend.redis import get_redis_client
from typing import Tuple, List

r = get_redis_client()

# create message history object for a user if not there
def create_default_user_hist(number):
    key = number
    data = {
        "current_convo_type": "main",
        "main_memory": [],
        "create_goal_memory": [],
        "current_field_entries": {},
    }

    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


# get a user's stored data
def get_user_hist(number):
    key = number
    json_data_retrieved = r.hget(str(key), "data")

    if not json_data_retrieved:
        create_default_user_hist(number)
        json_data_retrieved = r.hget(str(key), "data")

    data_retrieved = json.loads(json_data_retrieved)

    return data_retrieved


# update a user's convo type ONLY
def update_user_convo_type(number, convo_type):
    if convo_type != "main" and convo_type != "create_goal":
        raise Exception("Invalid convo type.")

    key = number
    data = get_user_hist(key)

    data["current_convo_type"] = convo_type

    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


# update a user's message history ONLY
def update_user_msg_memory(number, convo_type, messages):
    if convo_type not in ["main", "create_goal"]:
        raise Exception("Invalid convo type.")
    if type(messages) is not list:
        raise Exception("Invalid type for messages.")

    key = number
    data = get_user_hist(key)

    if convo_type == "main":
        data["main_memory"] = messages
    else:
        data["create_goal_memory"] = messages

    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


def update_current_goal_creation_field_entries(number, field_entries):
    key = number
    data = get_user_hist(key)

    data["current_field_entries"] = field_entries
    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)


def reset_current_goal_creation_field_entries(number):
    key = number
    data = get_user_hist(key)

    data["current_field_entries"] = {}
    json_data = json.dumps(data)
    r.hset(str(key), "data", json_data)