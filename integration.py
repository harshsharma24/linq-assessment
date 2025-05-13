# integration-service/integration.py
from flask import Blueprint, request, jsonify
from acme_client import AcmeClient

integration_bp = Blueprint('integration', __name__)

# Point at the same server since both run on one port
acme = AcmeClient(
    base_url="http://127.0.0.1:5000",
    client_id="foo",
    client_secret="bar"
)

def map_to_acme(body):
    return {
        "acme_first_name": body.get("firstName"),
        "acme_last_name":  body.get("lastName"),
        "acme_email":      body.get("email")
    }

def map_from_acme(data):
    return {
        "id":        data["id"],
        "firstName": data["acme_first_name"],
        "lastName":  data["acme_last_name"],
        "email":     data["acme_email"]
    }

@integration_bp.route("/contacts", methods=["POST"])
def create_contact():
    body = request.get_json() or {}
    try:
        crm = acme.create_contact(map_to_acme(body))
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify(map_from_acme(crm)), 201

@integration_bp.route("/contacts/<contact_id>", methods=["GET"])
def get_contact(contact_id):
    try:
        crm = acme.get_contact(contact_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify(map_from_acme(crm)), 200

@integration_bp.route("/contacts/<contact_id>", methods=["PUT"])
def update_contact(contact_id):
    updates = request.get_json() or {}
    acme_updates = {f"acme_{k}": v for k, v in updates.items()}
    try:
        crm = acme.update_contact(contact_id, acme_updates)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify(map_from_acme(crm)), 200

@integration_bp.route("/contacts/<contact_id>", methods=["DELETE"])
def delete_contact(contact_id):
    try:
        success = acme.delete_contact(contact_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return ('', 204) if success else (jsonify({"error": "not found"}), 404)