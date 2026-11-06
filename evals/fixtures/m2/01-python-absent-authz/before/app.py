from flask import Flask, jsonify

from auth import require_admin

app = Flask(__name__)


@app.get("/admin/users")
@require_admin
def list_users():
    return jsonify([{"id": 1, "email": "a@example.com"}])
