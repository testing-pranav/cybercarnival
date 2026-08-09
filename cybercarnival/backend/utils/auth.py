from functools import wraps
from flask import session, redirect, url_for, jsonify, request


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_username"):
            if request.path.startswith("/admin/api/"):
                return jsonify({"error": "authentication required"}), 401
            return redirect(url_for("admin_auth.login_page", next=request.path))
        return view(*args, **kwargs)

    return wrapped
