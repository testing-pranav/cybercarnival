from flask import Blueprint, request, jsonify

from extensions import limiter
from services.registration_service import (
    create_registration,
    DuplicateRegistrationError,
    EventNotFoundError,
)
from utils.validators import validate_registration_payload, ValidationError
from utils.logger import get_logger

bp = Blueprint("registration", __name__)
logger = get_logger("registration")


@bp.post("/api/registrations")
@limiter.limit("5 per minute")
def submit_registration():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "request body must be valid JSON"}), 400

    try:
        clean = validate_registration_payload(payload)
    except ValidationError as e:
        return jsonify({"error": "validation failed", "fields": e.errors}), 422

    try:
        record = create_registration(clean)
    except EventNotFoundError:
        return jsonify({"error": "unknown or inactive event_id"}), 404
    except DuplicateRegistrationError:
        return jsonify({"error": "this email is already registered for this event"}), 409

    logger.info("registration created id=%s event=%s", record["id"], record["event_id"])
    return jsonify({"id": record["id"], "status": record["status"]}), 201
