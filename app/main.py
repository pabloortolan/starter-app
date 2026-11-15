"""
A tiny web app to learn Docker, GitHub and cloud basics.

Endpoints:
  GET /         -> HTML page with a visit counter (stored in Redis)
  GET /health   -> health check used by Docker and cloud platforms
  GET /info     -> shows which container answered (useful when you scale)
"""
import os
import socket
from datetime import datetime, timezone

import redis
from flask import Flask, jsonify, render_template_string

APP_VERSION = os.getenv("APP_VERSION", "dev")
APP_ENV = os.getenv("APP_ENV", "local")

PAGE = """
<!doctype html>
<html>
<head>
  <title>Docker Starter App</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 60px auto; padding: 0 20px; }
    .count { font-size: 64px; font-weight: bold; color: #2563eb; }
    code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
    .muted { color: #64748b; font-size: 14px; }
  </style>
</head>
<body>
  <h1>Hello from a container 🐳</h1>
  <p>This page has been visited</p>
  <div class="count">{{ count }}</div>
  <p>times.</p>
  <hr>
  <p class="muted">
    Served by container <code>{{ hostname }}</code><br>
    Environment <code>{{ env }}</code> · Version <code>{{ version }}</code><br>
    Redis: <code>{{ redis_status }}</code>
  </p>
</body>
</html>
"""


def create_app(redis_client=None):
    app = Flask(__name__)

    if redis_client is None:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            socket_connect_timeout=1,
            decode_responses=True,
        )

    def increment_visits():
        try:
            return redis_client.incr("visits"), "connected"
        except redis.exceptions.RedisError:
            # The app keeps working without Redis, it just can't count.
            return "?", "unavailable"

    @app.get("/")
    def index():
        count, redis_status = increment_visits()
        return render_template_string(
            PAGE,
            count=count,
            hostname=socket.gethostname(),
            env=APP_ENV,
            version=APP_VERSION,
            redis_status=redis_status,
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/info")
    def info():
        return jsonify(
            hostname=socket.gethostname(),
            env=APP_ENV,
            version=APP_VERSION,
            time=datetime.now(timezone.utc).isoformat(),
        )

    return app


# Gunicorn (the production web server) looks for this variable.
app = create_app()

if __name__ == "__main__":
    app.run(
    host="0.0.0.0",  # nosec B104 - must listen on all interfaces inside a container
    port=int(os.getenv("PORT", "8000")),
    debug=os.getenv("FLASK_DEBUG") == "1")