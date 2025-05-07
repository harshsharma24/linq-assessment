from flask import Blueprint, request, jsonify, abort
import jwt, time, uuid
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mock_db import create_contact as db_create, get_contact as db_get, update_contact as db_update, delete_contact as db_delete

# JWT configuration
JWT_SECRET = "my_super_secret"
JWT_ALGORITHM = "HS256"

# Rate limiter (initialized in app)
limiter = Limiter(key_func=get_remote_address)

acme_bp = Blueprint('acme', __name__)

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            abort(401, "Missing or invalid Authorization header")
        token = auth_header.split(None, 1)[1]
        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError:
            abort(401, "Invalid or expired token")
        return f(*args, **kwargs)
    return wrapper

@acme_bp.route("/token", methods=["POST"])
def issue_token():
    """Issue a JWT valid for 1 hour (no credential check)."""
    payload = {"iss": "acme", "exp": time.time() + 3600}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return jsonify(access_token=token, expires_in=3600), 200

@acme_bp.route("/v1/acme/contacts", methods=["POST"])
@limiter.limit("10 per minute")
@token_required
def create_contact():
    data = request.get_json() or {}
    record = db_create(data)
    return jsonify(record), 201

@acme_bp.route("/v1/acme/contacts/<contact_id>", methods=["GET"])
@limiter.limit("20 per minute")
@token_required
def get_contact(contact_id):
    contact = db_get(contact_id)
    if not contact:
        abort(404, "Contact not found")
    return jsonify(contact), 200

@acme_bp.route("/v1/acme/contacts/<contact_id>", methods=["PUT"])
@limiter.limit("10 per minute")
@token_required
def update_contact(contact_id):
    updates = request.get_json() or {}
    updated = db_update(contact_id, updates)
    if not updated:
        abort(404, "Contact not found")
    return jsonify(updated), 200

@acme_bp.route("/v1/acme/contacts/<contact_id>", methods=["DELETE"])
@limiter.limit("5 per minute")
@token_required
def delete_contact(contact_id):
    deleted = db_delete(contact_id)
    if not deleted:
        abort(404, "Contact not found")
    return '', 204
