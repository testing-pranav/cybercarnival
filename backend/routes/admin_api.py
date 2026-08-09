import csv
import io

from flask import Blueprint, request, jsonify, session, Response

from utils.auth import login_required
from utils.logger import get_logger
from services import registration_service as regs
from services import event_service as events
from services import audit_service

bp = Blueprint("admin_api", __name__, url_prefix="/admin/api")
logger = get_logger("admin_api")


def _actor():
    return session.get("admin_username", "unknown")


def _ip():
    return request.remote_addr or "unknown"


# --- Summary -----------------------------------------------------------------------

@bp.get("/summary")
@login_required
def summary():
    all_events = events.list_events()
    counts = regs.counts_by_event()
    return jsonify(
        {
            "total_registrations": sum(counts.values()),
            "total_events": len(all_events),
            "by_event": [
                {"event_id": e["id"], "event_name": e["name"], "count": counts.get(e["id"], 0)}
                for e in all_events
            ],
        }
    )


# --- Registrations -------------------------------------------------------------------

@bp.get("/registrations")
@login_required
def list_registrations():
    event_id = request.args.get("event_id") or None
    return jsonify(regs.list_registrations(event_id))


@bp.get("/registrations/export.csv")
@login_required
def export_registrations_csv():
    event_id = request.args.get("event_id") or None
    records = regs.list_registrations(event_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "event_id", "name", "email", "phone", "college", "team_members", "status", "created_at"])
    for r in records:
        writer.writerow(
            [
                r["id"],
                r["event_id"],
                r["name"],
                r["email"],
                r["phone"],
                r.get("college", ""),
                "; ".join(r.get("team_members", [])),
                r["status"],
                r["created_at"],
            ]
        )

    audit_service.log_action(_actor(), "export_csv", f"exported registrations (event_id={event_id})", _ip())
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=registrations.csv"},
    )


@bp.post("/registrations/<registration_id>/status")
@login_required
def update_registration_status(registration_id):
    body = request.get_json(silent=True) or {}
    status = body.get("status")
    try:
        ok = regs.set_status(registration_id, status)
    except ValueError:
        return jsonify({"error": "invalid status"}), 422
    if not ok:
        return jsonify({"error": "not found"}), 404
    audit_service.log_action(_actor(), "update_status", f"registration {registration_id} -> {status}", _ip())
    return jsonify({"ok": True})


@bp.delete("/registrations/<registration_id>")
@login_required
def delete_registration(registration_id):
    ok = regs.delete_registration(registration_id)
    if not ok:
        return jsonify({"error": "not found"}), 404
    audit_service.log_action(_actor(), "delete_registration", f"registration {registration_id}", _ip())
    return jsonify({"ok": True})


# --- Events --------------------------------------------------------------------------

@bp.get("/events")
@login_required
def list_events():
    return jsonify(events.list_events())


@bp.post("/events")
@login_required
def create_event():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name or len(name) > 120:
        return jsonify({"error": "name is required (max 120 chars)"}), 422
    record = events.create_event(
        {
            "name": name,
            "fee": (body.get("fee") or "").strip()[:40],
            "team_size": (body.get("team_size") or "").strip()[:40],
            "venue": (body.get("venue") or "").strip()[:120],
            "date": (body.get("date") or "").strip()[:60],
        }
    )
    audit_service.log_action(_actor(), "create_event", f"event {record['id']} ({name})", _ip())
    return jsonify(record), 201


@bp.post("/events/<event_id>/toggle")
@login_required
def toggle_event(event_id):
    body = request.get_json(silent=True) or {}
    active = bool(body.get("active", True))
    ok = events.set_event_active(event_id, active)
    if not ok:
        return jsonify({"error": "not found"}), 404
    audit_service.log_action(_actor(), "toggle_event", f"event {event_id} active={active}", _ip())
    return jsonify({"ok": True})


@bp.delete("/events/<event_id>")
@login_required
def delete_event(event_id):
    ok = events.delete_event(event_id)
    if not ok:
        return jsonify({"error": "not found"}), 404
    audit_service.log_action(_actor(), "delete_event", f"event {event_id}", _ip())
    return jsonify({"ok": True})


# --- Audit log -------------------------------------------------------------------------

@bp.get("/audit-log")
@login_required
def audit_log():
    return jsonify(audit_service.list_audit_log())
