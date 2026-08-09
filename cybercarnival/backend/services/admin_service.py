import config
from storage import json_store
from utils.security import hash_password, verify_password
from utils.id_generator import new_uuid


def get_admin_by_username(username: str):
    for a in json_store.read_all(config.ADMINS_FILE):
        if a["username"] == username:
            return a
    return None


def verify_admin_credentials(username: str, password: str) -> bool:
    admin = get_admin_by_username(username)
    if not admin:
        # Still run a hash check against a dummy hash so responses take
        # roughly the same time whether the username exists or not
        # (mitigates username enumeration via timing).
        verify_password(password, hash_password("decoy-password-not-real"))
        return False
    return verify_password(password, admin["password_hash"])


def create_admin(username: str, plain_password: str) -> dict:
    if get_admin_by_username(username):
        raise ValueError("username already exists")
    record = {
        "id": new_uuid(),
        "username": username,
        "password_hash": hash_password(plain_password),
    }
    return json_store.append(config.ADMINS_FILE, record)
