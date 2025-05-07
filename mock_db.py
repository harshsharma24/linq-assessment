# mock-crm/mock_db.py
import uuid

# Simple in-memory store for contacts with default entries
STORE = {
    "1": {"id": "1", "acme_first_name": "John", "acme_last_name": "Doe", "acme_email": "john.doe@example.com"},
    "2": {"id": "2", "acme_first_name": "Jane", "acme_last_name": "Smith", "acme_email": "jane.smith@example.com"}
}

def create_contact(data):
    contact_id = str(uuid.uuid4())
    record = {**data, "id": contact_id}
    STORE[contact_id] = record
    return record

def get_contact(contact_id):
    return STORE.get(contact_id)

def update_contact(contact_id, updates):
    if contact_id in STORE:
        STORE[contact_id].update(updates)
        return STORE[contact_id]
    return None

def delete_contact(contact_id):
    return STORE.pop(contact_id, None)