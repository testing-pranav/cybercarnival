"""
Strict, allow-list style validation for all public input.
Never trust the client. Reject anything that doesn't match, don't try to
"fix" or reinterpret bad input.
"""
import re

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]{1,255}\.[a-zA-Z]{2,24}$")
PHONE_RE = re.compile(r"^[0-9+\-() ]{7,20}$")
# Letters (incl. common accented ranges), spaces, hyphens, apostrophes, dots.
NAME_RE = re.compile(r"^[A-Za-z .'\-]{2,80}$")
SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9 .,'\-&()/]{0,200}$")
ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


class ValidationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


def _strip(value) -> str:
    if not isinstance(value, str):
        raise ValueError("expected a string")
    # Strip control characters (defends against log injection / hidden payloads).
    cleaned = "".join(ch for ch in value if ch >= " " or ch == "\t")
    return cleaned.strip()


def validate_registration_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValidationError({"_": "request body must be a JSON object"})

    errors = {}
    clean = {}

    try:
        name = _strip(data.get("name", ""))
        if not NAME_RE.match(name):
            errors["name"] = "must be 2-80 letters/spaces/hyphens"
        clean["name"] = name
    except ValueError:
        errors["name"] = "invalid"

    try:
        email = _strip(data.get("email", "")).lower()
        if not EMAIL_RE.match(email):
            errors["email"] = "invalid email address"
        clean["email"] = email
    except ValueError:
        errors["email"] = "invalid"

    try:
        phone = _strip(data.get("phone", ""))
        if not PHONE_RE.match(phone):
            errors["phone"] = "invalid phone number"
        clean["phone"] = phone
    except ValueError:
        errors["phone"] = "invalid"

    try:
        event_id = _strip(data.get("event_id", ""))
        if not ID_RE.match(event_id):
            errors["event_id"] = "invalid event_id"
        clean["event_id"] = event_id
    except ValueError:
        errors["event_id"] = "invalid"

    try:
        college = _strip(data.get("college", ""))
        if college and not SAFE_TEXT_RE.match(college):
            errors["college"] = "contains unsupported characters"
        clean["college"] = college
    except ValueError:
        errors["college"] = "invalid"

    # Optional team member list — capped in size to prevent abuse.
    team_members = data.get("team_members", [])
    if team_members:
        if not isinstance(team_members, list) or len(team_members) > 10:
            errors["team_members"] = "must be a list of at most 10 names"
        else:
            cleaned_members = []
            for member in team_members:
                try:
                    m = _strip(member)
                except ValueError:
                    errors["team_members"] = "invalid member name"
                    break
                if not NAME_RE.match(m):
                    errors["team_members"] = "invalid member name"
                    break
                cleaned_members.append(m)
            else:
                clean["team_members"] = cleaned_members
    else:
        clean["team_members"] = []

    if errors:
        raise ValidationError(errors)
    return clean


def validate_login_payload(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValidationError({"_": "request body must be a JSON object"})
    username = _strip(data.get("username", ""))
    password = data.get("password", "")
    errors = {}
    if not username or len(username) > 64:
        errors["username"] = "required"
    if not isinstance(password, str) or not password or len(password) > 256:
        errors["password"] = "required"
    if errors:
        raise ValidationError(errors)
    return {"username": username, "password": password}
