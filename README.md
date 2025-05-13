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
   git clone https://github.com/your-username/contact-management-api.git
   cd contact-management-api
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
python app.py
```

The API will be accessible at `http://localhost:5000` by default.

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
pytest test_integration.py -v
```

Test suite includes:

* Contact creation tests
* Contact retrieval tests
* Contact update tests
* Contact deletion tests
* Error handling tests

## Design & Architecture

* **Modular Design**: Separates database operations from API endpoints
* **Field Mapping**: Transparent translation between your field names and ACME's
* **Error Handling**: Proper HTTP status codes and meaningful error messages
* **In-Memory Database**: Uses a simple dictionary-based store for demonstration purposes

## Future Improvements

* Replace in-memory store with a persistent database
* Add pagination for listing contacts
* Implement filtering and sorting capabilities
* Add authentication and authorization
* Create OpenAPI/Swagger documentation
* Add logging and monitoring
* Containerize with Docker for easier deployment

## Project Structure

```
.
├── app.py              # Main application entry point
├── db.py               # Database operations
├── requirements.txt    # Project dependencies
├── test_integration.py # Integration tests
└── README.md           # This documentation
```

## API Usage Examples

### Create a Contact

```bash
curl -X POST http://localhost:5000/api/contacts \
     -H "Content-Type: application/json" \
     -d '{"firstName":"Alice","lastName":"Smith","email":"alice@example.com"}'
```

### Get a Contact

```bash
curl -X GET http://localhost:5000/api/contacts/1
```

### Update a Contact

```bash
curl -X PUT http://localhost:5000/api/contacts/1 \
     -H "Content-Type: application/json" \
     -d '{"firstName":"Alice","lastName":"Johnson","email":"alice.johnson@example.com"}'
```

### Delete a Contact

```bash
curl -X DELETE http://localhost:5000/api/contacts/1
```

---
