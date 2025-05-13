import time
import pytest
import requests
import requests_mock
from acme_client import AcmeClient

BASE_URL = "http://testserver"

@pytest.fixture
def client():
    return AcmeClient(base_url=BASE_URL, client_id="foo", client_secret="bar", timeout=0.1)

def test_token_refresh_and_caching(client, requests_mock):
    # Mock /token
    requests_mock.post(f"{BASE_URL}/token", json={"access_token":"tok1","expires_in":2})
    # First call: should fetch a new token
    client._refresh_token_if_needed()
    assert client._token == "tok1"
    # advance time but still valid
    client._expiry = time.time() + 60
    # Next refresh should NOT call /token again
    requests_mock.reset()
    client._refresh_token_if_needed()
    assert not requests_mock.called

def test_create_contact_success(client, requests_mock):
    # stub token
    requests_mock.post(f"{BASE_URL}/token", json={"access_token":"tok","expires_in":3600})
    # stub create
    payload = {"acme_first_name":"A","acme_last_name":"B","acme_email":"a@b.c"}
    resp_obj = {**payload, "id":"123"}
    requests_mock.post(f"{BASE_URL}/v1/acme/contacts", json=resp_obj, status_code=201)
    out = client.create_contact(payload)
    assert out["id"] == "123"

def test_429_retries_then_success(client, requests_mock):
    requests_mock.post(f"{BASE_URL}/token", json={"access_token":"tok","expires_in":3600})
    url = f"{BASE_URL}/v1/acme/contacts"
    # first two requests 429, third OK
    adapter = requests_mock.post(url, [
        {"status_code":429, "headers":{"Retry-After":"0"}},
        {"status_code":500},
        {"json": {"id":"xyz"}, "status_code":201}
    ])
    out = client.create_contact({"acme_first_name":"X"})
    assert out["id"] == "xyz"
    # ensure exactly 3 attempts
    assert adapter.call_count == 3
