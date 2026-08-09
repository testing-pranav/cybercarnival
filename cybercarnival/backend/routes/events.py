from flask import Blueprint, jsonify
from services import event_service

bp = Blueprint("events", __name__)


@bp.get("/api/events")
def list_events():
    events = [e for e in event_service.list_events() if e.get("active", True)]
    # Never expose internal-only fields (there are none currently, but keep the
    # allow-list pattern so nothing new leaks by accident later).
    safe = [
        {
            "id": e["id"],
            "name": e["name"],
            "fee": e.get("fee", ""),
            "team_size": e.get("team_size", ""),
            "venue": e.get("venue", ""),
            "date": e.get("date", ""),
        }
        for e in events
    ]
    return jsonify(safe)
