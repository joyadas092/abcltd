# ban_manager.py

BANNED_USERS = set()

def is_banned(user_id: int) -> bool:
    return user_id in BANNED_USERS

def ban_user(user_id: int):
    BANNED_USERS.add(user_id)

def unban_user(user_id: int):
    BANNED_USERS.discard(user_id)

def get_all_banned():
    return list(BANNED_USERS)

import json
import os

FILE = "banned_users.json"

# Load on startup
if os.path.exists(FILE):
    with open(FILE, "r") as f:
        try:
            BANNED_USERS = set(json.load(f))
        except:
            BANNED_USERS = set()
else:
    BANNED_USERS = set()


def save():
    with open(FILE, "w") as f:
        json.dump(list(BANNED_USERS), f)


def is_banned(user_id: int) -> bool:
    return user_id in BANNED_USERS


def ban_user(user_id: int):
    BANNED_USERS.add(user_id)
    save()


def unban_user(user_id: int):
    BANNED_USERS.discard(user_id)
    save()