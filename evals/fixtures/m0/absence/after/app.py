from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/admin/users")
def list_users():
    return jsonify([{"id": 1, "email": "a@example.com"}])
