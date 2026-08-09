import time
import config
from storage import json_store
from utils.id_generator import new_uuid


class DuplicateRegistrationError(Exception):
    pass


class EventNotFoundError(Exception):
    pass


def create_registration(clean_data: dict) -> dict:
    from services.event_service import get_event

    event = get_event(clean_data["event_id"])
    if not event or not event.get("active", True):
        raise EventNotFoundError(clean_data["event_id"])

    # Idempotency: same email registering twice for the same event is rejected,
    # not silently duplicated. Prevents accidental double-submits and abuse.
    existing = json_store.read_all(config.REGISTRATIONS_FILE)
    for r in existing:
        if r["event_id"] == clean_data["event_id"] and r["email"] == clean_data["email"]:
            raise DuplicateRegistrationError(r["id"])

    record = {
        "id": new_uuid(),
        "event_id": clean_data["event_id"],
        "name": clean_data["name"],
        "email": clean_data["email"],
        "phone": clean_data["phone"],
        "college": clean_data.get("college", ""),
        "team_members": clean_data.get("team_members", []),
        "status": "pending",
        "created_at": time.time(),
    }
    return json_store.append(config.REGISTRATIONS_FILE, record)


def list_registrations(event_id: str = None) -> list:
    records = json_store.read_all(config.REGISTRATIONS_FILE)
    if event_id:
        records = [r for r in records if r["event_id"] == event_id]
    records.sort(key=lambda r: r["created_at"], reverse=True)
    return records


def get_registration(registration_id: str):
    for r in json_store.read_all(config.REGISTRATIONS_FILE):
        if r["id"] == registration_id:
            return r
    return None


def set_status(registration_id: str, status: str) -> bool:
    allowed = {"pending", "confirmed", "cancelled"}
    if status not in allowed:
        raise ValueError("invalid status")
    return json_store.update_where(
        config.REGISTRATIONS_FILE,
        lambda r: r["id"] == registration_id,
        lambda r: {**r, "status": status},
    )


def delete_registration(registration_id: str) -> bool:
    return json_store.delete_where(config.REGISTRATIONS_FILE, lambda r: r["id"] == registration_id)


def counts_by_event() -> dict:
    records = json_store.read_all(config.REGISTRATIONS_FILE)
    counts = {}
    for r in records:
        counts[r["event_id"]] = counts.get(r["event_id"], 0) + 1
    return counts
