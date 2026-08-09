import uuid


def new_uuid() -> str:
    """UUID4 registration/record ID. Stable, unguessable, safe to expose to the client."""
    return str(uuid.uuid4())
