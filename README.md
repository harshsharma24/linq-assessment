# Contact Management API

A lightweight Flask-based API that provides a standardized interface for managing contacts while translating between your application's field names and ACME's field naming conventions.

## Overview

This API serves as a bridge between your application and the ACME contact management system. It handles the field name mapping and provides a clean RESTful interface for managing contacts.

## Prerequisites

* Python 3.8+
* `pip` package manager

## Installation & Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/harshsharma24/linq-assessment.git
 
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate       # macOS/Linux
   # .\venv\Scripts\Activate.ps1  # Windows PowerShell
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Running the API

Start the Flask server:

```bash
flask run
```

The API will be accessible at `http://127.0.0.1:5000` by default.

## API Endpoints

### Contacts API

* **Create a contact**

  * `POST /api/contacts`
  * Request body: `{"firstName": "John", "lastName": "Doe", "email": "john.doe@example.com"}`

* **Get a contact**

  * `GET /api/contacts/<contact_id>`

* **Update a contact**

  * `PUT /api/contacts/<contact_id>`
  * Request body: `{"firstName": "John", "lastName": "Smith", "email": "john.smith@example.com"}`

* **Delete a contact**

  * `DELETE /api/contacts/<contact_id>`

## Field Mapping

This API handles field name translation between your application and ACME's system:

| Your API Field | ACME Field        |
| -------------- | ----------------- |
| `firstName`    | `acme_first_name` |
| `lastName`     | `acme_last_name`  |
| `email`        | `acme_email`      |

## Testing

The API includes comprehensive test coverage for all CRUD operations:

```bash
pytest --maxfail=1 --disable-warnings -q
```

Test suite includes:

* Contact creation tests
* Contact retrieval tests
* Contact update tests
* Contact deletion tests
* Error handling tests

## Design & Architecture

## Trade‑Offs

* **In-Memory Queue:** Used a Python `queue.Queue` for fast MVP development and zero external dependencies, at the cost of no persistence across restarts.
* **In-Memory DB (Hash Map):** Contacts are stored in a simple dict for quick prototyping; data resets on service restart.
* **Mocked ACME Responses:** The ACME backend is fully mocked, enabling local development and controlled testing, but lacking real-world API semantics and error rates.

## Design & Architecture

Below are the core architectural choices, why they were made, and how they work together:

### 1. Modular Design & Blueprint Separation

* **`acme.py` + `mock_db.py`** implement your *mock CRM* as a self‑contained Flask Blueprint. All HTTP routes, JWT logic, rate‑limiter and webhook dispatch live here.
* **`acme_client.py`** encapsulates *all* downstream communication: token refresh, timeouts, and retry/back‑off. Your Flask handlers never call `requests` directly—they just call `AcmeClient` methods.
* **`integration.py`** exposes your own client‑facing CRUD under `/api/contacts`, mapping fields and translating errors into clean JSON responses.

By isolating these layers, you can:

1. **Swap** any one component (e.g., replace the in‑memory queue with Celery) without touching the others.
2. **Test** each piece in isolation (unit tests on `AcmeClient`, integration tests on your Flask endpoints).
3. **Read** and reason about each responsibility without wading through unrelated code.

### 2. Field Mapping & Data Normalization

* Internal model: `{ firstName, lastName, email }`
* Acme CRM model: `{ acme_first_name, acme_last_name, acme_email }`

Two simple helper functions (`map_to_acme`, `map_from_acme`) handle this translation:

1. **Forward mapping** converts your payload into Acme’s schema for all outbound calls.
2. **Backward mapping** converts CRM responses back into your normalized interface.

This pattern ensures your front‑end or calling code never has to know about Acme’s naming conventions, and makes it easy to add more fields or support additional CRMs in the future.

### 3. Resiliency & Error Handling

* **Timeouts**: Every HTTP request has a strict 5s timeout, preventing your service from hanging on slow dependencies.
* **Automatic JWT Refresh**: `AcmeClient` caches tokens and refreshes them 60s before expiry, so you never get caught with an expired token in mid‑flow.
* **Exponential Back‑Off Retries**: On 429 (rate limit) or any 5xx error, Tenacity retries with delays of 6s → 12s → 24s → 48s (capped at 60s), up to 5 attempts. This smooths spikes and gracefully recovers from transient outages.
* **HTTP Status Codes**: The Flask handlers map errors to the correct status: 401 for auth, 404 for missing resources, 429 for rate limits, and 502 for upstream failures in the integration layer.

### 4. Rate Limiting Simulation

* We use `flask-limiter` to simulate realistic API quotas on the mock CRM:

  * **10 req/min** for create/update
  * **10 req/min** for reads
  * **10 req/min** for deletes
* Each rate‑limited endpoint returns 429 with a `Retry-After` header. Your client’s back‑off logic reads this and respects the wait time.

This demonstrates how your integration code would behave under real API constraints.

### 5. Asynchronous Webhooks & Queueing

* **Dispatch**: Outbound webhooks fire-and-forget via daemon threads, so your create/update HTTP response never blocks on network I/O.
* **Ingestion**: Received webhooks land in an in‑memory `queue.Queue`, and a dedicated background thread (`process_webhook_queue`) pulls items off for downstream processing.

This decoupling ensures smooth, non‑blocking flows and lays the groundwork for swapping in a durable broker (e.g., RabbitMQ, AWS SQS) or Celery workers.

### 6. In-Memory Data Store

* We use a simple Python dictionary (`STORE`) in `mock_db.py` for both the mock CRM and for stubbing in tests.
* **Benefits**: zero external dependencies, instant startup, and easy inspection.
* **Trade‑off**: data is lost on process restart. For production, you’d replace this with a real database (PostgreSQL, DynamoDB, etc.).

## Postman Collection

A Postman collection is included for manual testing:

* Import **Linq Assessment.postman\_collection.json** into Postman
* Use the collection to test all API endpoints

## Design & Architecture

* **Modular Design**

  * **API Layer (`integration.py`)**: Exposes RESTful endpoints and handles HTTP requests/responses
  * **Client Layer (`acme_client.py`)**: Manages communication with the ACME CRM API
  * **Mock ACME API (`acme.py`)**: Simulates the ACME CRM system for testing
  * **Database Layer (`mock_db.py`)**: Provides data storage and retrieval functions

* **Field Mapping**

  * Transparent translation between your application's field names and ACME's field names
  * Mapping is handled in the integration layer, shielding clients from ACME's specific naming requirements

* **Error Handling**

  * Proper HTTP status codes (`200`, `201`, `204`, `400`, `404`, `500`)
  * Meaningful error messages to help clients understand issues
  * Exception handling to prevent internal errors from reaching clients

* **In-Memory Database**

  * Dictionary-based storage for demonstration and testing
  * UUID-based identifiers for contacts
  * Clean interface that mimics a real database for easy future migration

## Future Improvements

* **Message Queuing System**: Implement ActiveMQ, RabbitMQ, or AWS SQS to:

  * Ensure reliable message delivery between components
  * Provide fault tolerance for system outages
  * Enable asynchronous processing of requests
  * Support horizontal scaling of workers

* **Pagination for List Endpoints**:

  * Add `limit` and `offset` parameters to GET endpoints
  * Implement cursor-based pagination for better performance with large datasets
  * Include metadata in responses (total count, next/previous links)
  * Allow customizable page sizes

* **Caching Layer**:

  * Implement Redis or Memcached for high-performance caching
  * Cache frequently accessed contacts to reduce database load
  * Add cache invalidation strategies for data consistency
  * Support configurable TTL (Time-To-Live) for cached items

* **Containerization**:

  * Create Docker images for consistent deployment
  * Develop `docker-compose` setup for local development
  * Design Kubernetes manifests for production deployment
  * Implement health checks and container orchestration

* **Persistent Database**:

  * Replace in-memory store with PostgreSQL or MongoDB
  * Implement proper database migration strategy
  * Add connection pooling for performance optimization
  * Design appropriate indexes for query optimization

* **Enhanced Logging and Monitoring**:

  * Implement structured logging (JSON format)
  * Add request tracing with unique correlation IDs
  * Set up Prometheus metrics for performance monitoring
  * Create Grafana dashboards for visualization
  * Configure alerting for critical errors and performance issues

* **OpenAPI Documentation**:

  * Generate Swagger/OpenAPI specification
  * Implement interactive documentation UI
  * Include example requests and responses
  * Document error codes and handling
  * Provide SDK generation capabilities

## Repository

* GitHub: [https://github.com/harshsharma24/linq-assessment.git]

## Testing

Run all tests with:

```bash
pytest --maxfail=1 --disable-warnings -q
```
