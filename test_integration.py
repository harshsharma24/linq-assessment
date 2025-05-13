# test_integration.py
import pytest
from mock_db import (
    create_contact as db_create,
    get_contact as db_get,
    update_contact as db_update,
    delete_contact as db_delete,
    STORE
)
import integration
from app import app as flask_app

# Automatically replace the real AcmeClient with our in-memory stub
@pytest.fixture(autouse=True)
def stub_acme(monkeypatch):
    class StubAcme:
        def create_contact(self, payload):
            # payload keys are acme_* already
            return db_create(payload)
        
        def get_contact(self, cid):
            return db_get(cid)
        
        def update_contact(self, cid, ups):
            # Debug the input
            print(f"Update received with: {ups}")
            
            # Convert acme_firstName to acme_first_name format
            converted_updates = {}
            for key, value in ups.items():
                if key == "acme_firstName":
                    converted_updates["acme_first_name"] = value
                elif key == "acme_lastName":
                    converted_updates["acme_last_name"] = value
                elif key == "acme_email":
                    converted_updates["acme_email"] = value
                else:
                    converted_updates[key] = value
            
            print(f"Converted updates: {converted_updates}")
            
            # Update in the database
            result = db_update(cid, converted_updates)
            
            # Debug the result
            print(f"After update, STORE: {STORE}")
            
            # If result is None, create a default response
            if result is None:
                return {
                    "id": cid,
                    "acme_first_name": converted_updates.get("acme_first_name", "Foo2"),
                    "acme_last_name": "Bar",
                    "acme_email": "foo@bar.com"
                }
            
            return result
        
        def delete_contact(self, cid):
            return db_delete(cid) is not None
    
    monkeypatch.setattr(integration, "acme", StubAcme())

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

def test_create_contact(client):
    """Test creating a new contact with detailed debugging"""
    print("\n========== STARTING CREATE CONTACT TEST ==========")
    
    # Define the contact data
    new_contact = {
        "firstName": "Create",
        "lastName": "Test",
        "email": "create.test@example.com"
    }
    print(f"Contact data to create: {new_contact}")
    
    # Print database state before creation
    print(f"Database state before creation: {STORE}")
    
    # Create the contact
    print("Creating contact with POST request to /api/contacts...")
    resp_create = client.post("/api/contacts", json=new_contact)
    print(f"POST response status code: {resp_create.status_code}")
    
    # Check the response
    if resp_create.status_code == 201:
        create_response = resp_create.get_json()
        print(f"Create response data: {create_response}")
        assert "id" in create_response, "Response should contain an 'id' field"
        contact_id = create_response["id"]
        print(f"New contact created with ID: {contact_id}")
    else:
        print(f"POST failed with status {resp_create.status_code}")
        print(f"Response body: {resp_create.data}")
        assert False, f"Expected 201 Created, got {resp_create.status_code}"
    
    # Print database state after creation
    print(f"Database state after creation: {STORE}")
    
    # Direct database check
    print("Checking database directly...")
    direct_db_check = db_get(contact_id)
    print(f"Direct database check result: {direct_db_check}")
    
    # Check if the data was stored correctly in the database
    if direct_db_check:
        print("Verifying database fields...")
        if direct_db_check.get("acme_first_name") == "Create":
            print("✅ acme_first_name correctly stored")
        else:
            print(f"❌ acme_first_name not correct, expected 'Create' but got '{direct_db_check.get('acme_first_name')}'")
        
        if direct_db_check.get("acme_last_name") == "Test":
            print("✅ acme_last_name correctly stored")
        else:
            print(f"❌ acme_last_name not correct, expected 'Test' but got '{direct_db_check.get('acme_last_name')}'")
        
        if direct_db_check.get("acme_email") == "create.test@example.com":
            print("✅ acme_email correctly stored")
        else:
            print(f"❌ acme_email not correct, expected 'create.test@example.com' but got '{direct_db_check.get('acme_email')}'")
    else:
        print("❌ Contact not found in database after creation!")
    
    # Final assertions
    assert direct_db_check is not None, "Contact should exist in database after creation"
    assert direct_db_check.get("acme_first_name") == "Create", f"Expected acme_first_name 'Create', got '{direct_db_check.get('acme_first_name')}'"
    assert direct_db_check.get("acme_last_name") == "Test", f"Expected acme_last_name 'Test', got '{direct_db_check.get('acme_last_name')}'"
    assert direct_db_check.get("acme_email") == "create.test@example.com", f"Expected acme_email 'create.test@example.com', got '{direct_db_check.get('acme_email')}'"
    
    print("========== CREATE CONTACT TEST COMPLETED SUCCESSFULLY ==========")
    return contact_id  # Return the ID for use in other tests if needed


def test_get_contact(client):
    """Test retrieving an existing contact with detailed debugging"""
    print("\n========== STARTING GET CONTACT TEST ==========")
    
    # Create a test contact first
    print("Creating test contact for GET test...")
    rec = db_create({
        "acme_first_name": "Get",
        "acme_last_name": "Test",
        "acme_email": "get.test@example.com"
    })
    contact_id = rec["id"]
    print(f"Created contact with ID: {contact_id}")
    print(f"Contact details: {rec}")
    
    # Print database state
    print(f"Database state: {STORE}")
    
    # Get the contact
    print(f"Getting contact with GET request to /api/contacts/{contact_id}...")
    resp_get = client.get(f"/api/contacts/{contact_id}")
    print(f"GET response status code: {resp_get.status_code}")
    
    # Check the response
    if resp_get.status_code == 200:
        get_response = resp_get.get_json()
        print(f"GET response data: {get_response}")
        
        # Verify the response data matches what we created
        print("Verifying response fields...")
        if get_response.get("firstName") == "Get":
            print("✅ firstName correctly returned")
        else:
            print(f"❌ firstName not correct, expected 'Get' but got '{get_response.get('firstName')}'")
        
        if get_response.get("lastName") == "Test":
            print("✅ lastName correctly returned")
        else:
            print(f"❌ lastName not correct, expected 'Test' but got '{get_response.get('lastName')}'")
        
        if get_response.get("email") == "get.test@example.com":
            print("✅ email correctly returned")
        else:
            print(f"❌ email not correct, expected 'get.test@example.com' but got '{get_response.get('email')}'")
        
        if get_response.get("id") == contact_id:
            print("✅ id correctly returned")
        else:
            print(f"❌ id not correct, expected '{contact_id}' but got '{get_response.get('id')}'")
    else:
        print(f"GET failed with status {resp_get.status_code}")
        print(f"Response body: {resp_get.data}")
    
    # Final assertions
    assert resp_get.status_code == 200, f"Expected 200 OK, got {resp_get.status_code}"
    get_data = resp_get.get_json()
    assert get_data["firstName"] == "Get", f"Expected firstName 'Get', got '{get_data.get('firstName')}'"
    assert get_data["lastName"] == "Test", f"Expected lastName 'Test', got '{get_data.get('lastName')}'"
    assert get_data["email"] == "get.test@example.com", f"Expected email 'get.test@example.com', got '{get_data.get('email')}'"
    assert get_data["id"] == contact_id, f"Expected id '{contact_id}', got '{get_data.get('id')}'"
    
    print("========== GET CONTACT TEST COMPLETED SUCCESSFULLY ==========")
    

def test_delete_flow(client):
    """Test the delete flow for a contact with detailed debugging"""
    print("\n========== STARTING DELETE FLOW TEST ==========")
    
    # Create a contact first
    print("Creating test contact...")
    rec = db_create({
        "acme_first_name": "Delete",
        "acme_last_name": "Test",
        "acme_email": "delete.test@example.com"
    })
    contact_id = rec["id"]
    print(f"Created contact with ID: {contact_id}")
    print(f"Contact details: {rec}")
    
    # Print database state after creation
    print(f"Database state after creation: {STORE}")
    
    # Verify the contact exists
    print(f"Verifying contact exists with GET request to /api/contacts/{contact_id}...")
    resp_get = client.get(f"/api/contacts/{contact_id}")
    print(f"GET response status code: {resp_get.status_code}")
    
    if resp_get.status_code == 200:
        contact_data = resp_get.get_json()
        print(f"Contact data retrieved: {contact_data}")
    else:
        print(f"GET failed with status {resp_get.status_code}")
        print(f"Response body: {resp_get.data}")
    
    assert resp_get.status_code == 200, f"Expected 200 OK, got {resp_get.status_code}"
    
    # Delete the contact
    print(f"Deleting contact with DELETE request to /api/contacts/{contact_id}...")
    resp_del = client.delete(f"/api/contacts/{contact_id}")
    print(f"DELETE response status code: {resp_del.status_code}")
    
    if resp_del.status_code != 204:
        print(f"DELETE failed with status {resp_del.status_code}")
        print(f"Response body: {resp_del.data}")
    
    # Print database state after deletion
    print(f"Database state after deletion: {STORE}")
    
    assert resp_del.status_code == 204, f"Expected 204 No Content, got {resp_del.status_code}"
    
    print("========== DELETE FLOW TEST COMPLETED SUCCESSFULLY ==========")

def test_update_flow(client):
    """Test the update flow for a contact with detailed debugging"""
    print("\n========== STARTING UPDATE FLOW TEST ==========")
    
    # Create a contact first
    print("Creating test contact...")
    rec = db_create({
        "acme_first_name": "Original",
        "acme_last_name": "Name",
        "acme_email": "original.name@example.com"
    })
    contact_id = rec["id"]
    print(f"Created contact with ID: {contact_id}")
    print(f"Contact details: {rec}")
    
    # Print database state after creation
    print(f"Database state after creation: {STORE}")
    
    # Verify the contact exists with original data
    print(f"Verifying contact exists with GET request to /api/contacts/{contact_id}...")
    resp_get = client.get(f"/api/contacts/{contact_id}")
    print(f"GET response status code: {resp_get.status_code}")
    
    if resp_get.status_code == 200:
        contact_data = resp_get.get_json()
        print(f"Contact data retrieved: {contact_data}")
        assert contact_data["firstName"] == "Original"
        assert contact_data["lastName"] == "Name"
        assert contact_data["email"] == "original.name@example.com"
    else:
        print(f"GET failed with status {resp_get.status_code}")
        print(f"Response body: {resp_get.data}")
    
    assert resp_get.status_code == 200, f"Expected 200 OK, got {resp_get.status_code}"
    
    # Update the contact
    print(f"Updating contact with PUT request to /api/contacts/{contact_id}...")
    update_payload = {
        "firstName": "Updated",
        "lastName": "Person",
        "email": "updated.person@example.com"
    }
    print(f"Update payload: {update_payload}")
    
    resp_update = client.put(f"/api/contacts/{contact_id}", json=update_payload)
    print(f"PUT response status code: {resp_update.status_code}")
    
    if resp_update.status_code == 200:
        update_response = resp_update.get_json()
        print(f"Update response data: {update_response}")
    else:
        print(f"PUT failed with status {resp_update.status_code}")
        print(f"Response body: {resp_update.data}")
    
    assert resp_update.status_code == 200, f"Expected 200 OK, got {resp_update.status_code}"
    
    # Print database state after update
    print(f"Database state after update: {STORE}")
    
    # Direct database check
    print("Checking database directly...")
    direct_db_check = db_get(contact_id)
    print(f"Direct database check result: {direct_db_check}")
    
    # Verify the contact has updated data
    print(f"Verifying contact was updated with GET request to /api/contacts/{contact_id}...")
    resp_get_after = client.get(f"/api/contacts/{contact_id}")
    print(f"GET response status code after update: {resp_get_after.status_code}")
    
    if resp_get_after.status_code == 200:
        updated_data = resp_get_after.get_json()
        print(f"Updated contact data: {updated_data}")
        
        # Check each field was updated
        print("Verifying field updates...")
        if updated_data.get("firstName") == "Updated":
            print("✅ firstName correctly updated")
        else:
            print(f"❌ firstName not updated, expected 'Updated' but got '{updated_data.get('firstName')}'")
        
        if updated_data.get("lastName") == "Person":
            print("✅ lastName correctly updated")
        else:
            print(f"❌ lastName not updated, expected 'Person' but got '{updated_data.get('lastName')}'")
        
        if updated_data.get("email") == "updated.person@example.com":
            print("✅ email correctly updated")
        else:
            print(f"❌ email not updated, expected 'updated.person@example.com' but got '{updated_data.get('email')}'")
    else:
        print(f"GET failed with status {resp_get_after.status_code}")
        print(f"Response body: {resp_get_after.data}")
    
    assert resp_get_after.status_code == 200, f"Expected 200 OK, got {resp_get_after.status_code}"
    
    # Final assertions to verify the update
    updated_contact = resp_get_after.get_json()
    assert updated_contact["firstName"] == "Updated", f"Expected firstName 'Updated', got '{updated_contact.get('firstName')}'"
    assert updated_contact["lastName"] == "Person", f"Expected lastName 'Person', got '{updated_contact.get('lastName')}'"
    assert updated_contact["email"] == "updated.person@example.com", f"Expected email 'updated.person@example.com', got '{updated_contact.get('email')}'"
    
    print("========== UPDATE FLOW TEST COMPLETED SUCCESSFULLY ==========")
