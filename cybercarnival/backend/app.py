from flask import Flask, jsonify, render_template
from flask_cors import CORS

import config
from extensions import limiter, csrf
from utils.security import add_security_headers
from utils.logger import get_logger

from routes.health import bp as health_bp
from routes.events import bp as events_bp
from routes.registration import bp as registration_bp
from routes.admin_auth import bp as admin_auth_bp
from routes.admin_pages import bp as admin_pages_bp
from routes.admin_api import bp as admin_api_bp
from routes.frontend import bp as frontend_bp

logger = get_logger("app")


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
    app.config["SESSION_COOKIE_HTTPONLY"] = config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = config.SESSION_COOKIE_SAMESITE
    app.config["PERMANENT_SESSION_LIFETIME"] = config.PERMANENT_SESSION_LIFETIME_SECONDS

    limiter.init_app(app)
    csrf.init_app(app)

    # Public API is meant to be called cross-origin from the marketing frontend.
    # Admin routes are NOT included here — they're same-origin, cookie-authenticated only.
    CORS(
        app,
        resources={r"/api/*": {"origins": config.ALLOWED_ORIGINS or []}},
        supports_credentials=False,
        methods=["GET", "POST"],
    )

    app.register_blueprint(health_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(admin_pages_bp)
    app.register_blueprint(admin_api_bp)
    app.register_blueprint(frontend_bp)  # catch-all — must stay last

    # The public registration endpoint is called by client-side JS with no
    # Flask session/cookie, so it can't carry a CSRF token — CSRF protection
    # is meaningless there. It's still protected by strict input validation,
    # CORS allow-listing, and rate limiting.
    csrf.exempt(registration_bp)

    app.after_request(add_security_headers)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "request body too large"}), 413

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": "too many requests, slow down"}), 429

    @app.errorhandler(500)
    def server_error(e):
        logger.exception("unhandled server error")
        return jsonify({"error": "internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    # Dev server only. In production run behind gunicorn + a reverse proxy
    # (nginx/Caddy) terminating TLS. See README.md.
    app.run(host="127.0.0.1", port=5000, debug=not config.IS_PRODUCTION)
