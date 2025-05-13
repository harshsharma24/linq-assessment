import logging
from flask import Blueprint, request, jsonify, abort
import time, uuid, jwt
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import queue
from mock_db import (
    create_contact as db_create,
    get_contact    as db_get,
    update_contact as db_update,
    delete_contact as db_delete,
)
import requests
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET, JWT_ALGORITHM = "my_super_secret", "HS256"

# Rate limiter (initialized in app)
limiter = Limiter(key_func=get_remote_address)
acme_bp = Blueprint('acme', __name__)

# In-memory webhook subscribers
WEBHOOK_SUBSCRIBERS = [
    {"event": "contact.created", "url": "http://127.0.0.1:5000/webhooks/acme"},
    {"event": "contact.updated", "url": "http://127.0.0.1:5000/webhooks/acme"}
]

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            abort(401, "Missing or invalid Authorization header")
        token = auth.split(None, 1)[1]
        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError:
            logger.warning("Invalid or expired token")
            abort(401, "Invalid or expired token")
        return f(*args, **kwargs)
    return wrapper

@acme_bp.route("/token", methods=["POST"])
def issue_token():
    """Issue a JWT valid for 1 hour (no credential check)."""
    payload = {"iss": "acme", "exp": time.time() + 3600}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info("Issued new JWT")
    return jsonify(access_token=token, expires_in=3600), 200

def dispatch_webhook(event, payload):
    """Asynchronously POSTs a webhook to each subscriber of the given event."""
    body = {"event": event, "payload": payload}
    for sub in WEBHOOK_SUBSCRIBERS:
        if sub["event"] == event:
            url = sub["url"]
            logger.info(f"Hitting webhook for event='{event}' to url='{url}' with payload={payload}")
            def send(u, b):
                try:
                    logger.info(f"Successfully sent webhook to {u}")
                    resp = requests.post(u, json=b, timeout=5)
                    resp.raise_for_status()
                except Exception as e:
                    logger.error(f"Error sending webhook to {u}: {e}")
            Thread(target=send, args=(url, body), daemon=True).start()

@acme_bp.route("/v1/acme/contacts", methods=["POST"])
@limiter.limit("10 per minute")
@token_required
def create_contact():
    """Create contact and dispatch 'contact.created' webhook."""
    data = request.get_json() or {}
    record = db_create(data)
    logger.info(f"Contact created: {record}")
    dispatch_webhook("contact.created", record)
    return jsonify(record), 201

@acme_bp.route("/v1/acme/contacts/<contact_id>", methods=["PUT"])
@limiter.limit("10 per minute")
@token_required
def update_contact(contact_id):
    """Update contact and dispatch 'contact.updated' webhook."""
    updates = request.get_json() or {}
    record = db_update(contact_id, updates)
    if not record:
        logger.warning(f"Attempted update on missing contact ID {contact_id}")
        abort(404, "Contact not found")
    logger.info(f"Contact updated: {record}")
    dispatch_webhook("contact.updated", record)
    return jsonify(record), 200

@acme_bp.route("/v1/acme/contacts/<contact_id>", methods=["GET"])
@limiter.limit("20 per minute")
@token_required
def get_contact(contact_id):
    contact = db_get(contact_id)
    if not contact:
        logger.warning(f"Contact not found: {contact_id}")
        abort(404, "Contact not found")
    logger.info(f"Contact retrieved: {contact}")
    return jsonify(contact), 200

@acme_bp.route("/v1/acme/contacts/<contact_id>", methods=["DELETE"])
@limiter.limit("5 per minute")
@token_required
def delete_contact(contact_id):
    deleted = db_delete(contact_id)
    if not deleted:
        logger.warning(f"Attempted delete on missing contact ID {contact_id}")
        abort(404, "Contact not found")
    logger.info(f"Contact deleted: ID {contact_id}")
    return '', 204


WEBHOOK_QUEUE = queue.Queue()

@acme_bp.route("/webhooks/acme", methods=["POST"])
def receive_webhook():    
    event = request.json.get("event")
    payload = request.json.get("payload")
    logger.info(f"Received webhook for event='{event}' with payload={payload}")
    WEBHOOK_QUEUE.put((event, payload))
    logger.info(f"Queued webhook for event='{event}' with payload={payload}")
    return '', 200

def process_webhook_queue():
    while True:
        event, payload = WEBHOOK_QUEUE.get()
        logger.info(f"Event consumed from queue: event='{event}' with payload={payload}")
        WEBHOOK_QUEUE.task_done()

# Start the webhook queue processor
Thread(target=process_webhook_queue, daemon=True).start()
