import time
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class AcmeClient:
    # Base delay matching 10 req/min (one slot every 6s)
    BASE_DELAY = 6

    def __init__(self, base_url, client_id, client_secret, timeout=5):
        self.base_url      = base_url
        self.client_id     = client_id
        self.client_secret = client_secret
        self.timeout       = timeout
        self._token        = None
        self._expiry       = 0

    def _refresh_token_if_needed(self):
        now = time.time()
        if not self._token or now >= self._expiry:
            resp = requests.post(
                f"{self.base_url}/token",
                json={"client_id": self.client_id, "client_secret": self.client_secret},
                timeout=self.timeout
            )
            resp.raise_for_status()
            data = resp.json()
            self._token  = data["access_token"]
            # refresh 60s before true expiry
            self._expiry = now + data.get("expires_in", 3600) - 60

    def _headers(self):
        self._refresh_token_if_needed()
        return {"Authorization": f"Bearer {self._token}"}

    @retry(
        retry=retry_if_exception_type(requests.HTTPError),
        wait=wait_exponential(multiplier=BASE_DELAY, min=BASE_DELAY, max=60),
        stop=stop_after_attempt(5),
        reraise=True
    )
    def create_contact(self, payload):
        resp = requests.post(
            f"{self.base_url}/v1/acme/contacts",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout
        )
        if resp.status_code == 429 or resp.status_code >= 500:
            resp.raise_for_status()
        return resp.json()

    @retry(
        retry=retry_if_exception_type(requests.HTTPError),
        wait=wait_exponential(multiplier=BASE_DELAY, min=BASE_DELAY, max=60),
        stop=stop_after_attempt(5),
        reraise=True
    )
    def get_contact(self, contact_id):
        resp = requests.get(
            f"{self.base_url}/v1/acme/contacts/{contact_id}",
            headers=self._headers(),
            timeout=self.timeout
        )
        if resp.status_code == 429 or resp.status_code >= 500:
            resp.raise_for_status()
        return resp.json()

    @retry(
        retry=retry_if_exception_type(requests.HTTPError),
        wait=wait_exponential(multiplier=BASE_DELAY, min=BASE_DELAY, max=60),
        stop=stop_after_attempt(5),
        reraise=True
    )
    def update_contact(self, contact_id, updates):
        resp = requests.put(
            f"{self.base_url}/v1/acme/contacts/{contact_id}",
            json=updates,
            headers=self._headers(),
            timeout=self.timeout
        )
        if resp.status_code == 429 or resp.status_code >= 500:
            resp.raise_for_status()
        return resp.json()

    @retry(
        retry=retry_if_exception_type(requests.HTTPError),
        wait=wait_exponential(multiplier=BASE_DELAY, min=BASE_DELAY, max=60),
        stop=stop_after_attempt(5),
        reraise=True
    )
    def delete_contact(self, contact_id):
        resp = requests.delete(
            f"{self.base_url}/v1/acme/contacts/{contact_id}",
            headers=self._headers(),
            timeout=self.timeout
        )
        if resp.status_code == 429 or resp.status_code >= 500:
            resp.raise_for_status()
        return resp.status_code == 204