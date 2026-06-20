import json
import os


def app(environ, start_response):
    body = json.dumps({
        "ok": True,
        "has_database_url": bool(os.getenv("DATABASE_URL")),
        "has_session_secret": bool(os.getenv("SESSION_SECRET_KEY")),
        "database_url_prefix": (os.getenv("DATABASE_URL") or "")[:18],
    }).encode("utf-8")
    start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
    return [body]
