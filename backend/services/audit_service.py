import time
import config
from storage import json_store
from utils.id_generator import new_uuid


def log_action(actor: str, action: str, detail: str, ip: str) -> None:
    """Append-only audit trail. Never log secrets/passwords/tokens here."""
    json_store.append(
        config.AUDIT_LOG_FILE,
        {
            "id": new_uuid(),
            "timestamp": time.time(),
            "actor": actor,
            "action": action,
            "detail": detail,
            "ip": ip,
        },
    )


def list_audit_log(limit: int = 200) -> list:
    entries = json_store.read_all(config.AUDIT_LOG_FILE)
    entries.sort(key=lambda r: r["timestamp"], reverse=True)
    return entries[:limit]
