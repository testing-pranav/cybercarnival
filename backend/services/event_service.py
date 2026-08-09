import time
import config
from storage import json_store
from utils.id_generator import new_uuid


def list_events() -> list:
    return json_store.read_all(config.EVENTS_FILE)


def get_event(event_id: str):
    for e in list_events():
        if e["id"] == event_id:
            return e
    return None


def create_event(data: dict) -> dict:
    record = {
        "id": new_uuid(),
        "name": data["name"],
        "fee": data.get("fee", ""),
        "team_size": data.get("team_size", ""),
        "venue": data.get("venue", ""),
        "date": data.get("date", ""),
        "active": True,
        "created_at": time.time(),
    }
    return json_store.append(config.EVENTS_FILE, record)


def set_event_active(event_id: str, active: bool) -> bool:
    return json_store.update_where(
        config.EVENTS_FILE,
        lambda r: r["id"] == event_id,
        lambda r: {**r, "active": active},
    )


def delete_event(event_id: str) -> bool:
    return json_store.delete_where(config.EVENTS_FILE, lambda r: r["id"] == event_id)
