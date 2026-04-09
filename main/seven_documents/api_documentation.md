# API Documentation – DC48K Support Platform

## Document Metadata

| Field | Value |
|-------|-------|
| **Title** | DC48K Support Platform – API Documentation |
| **Author** | Serge Shema |
| **Date** | April 9, 2026 |
| **Version** | v1.0 |
| **API Version** | v1 |

---

## 1. API Overview

### 1.1 API Architecture

- **Architecture:** RESTful API with Django REST Framework
- **Base URL:** `https://api.dc48k.org/api/v1/`
- **Response Format:** JSON
- **Pagination:** Cursor-based pagination (default 20 items/page)
- **Rate Limiting:** 100 requests/minute per authenticated user

### 1.2 API Versioning

- **Current Version:** v1 (production)
- **Backward Compatibility:** Maintained through minor versions
- **Deprecation Policy:** 6-month notice before removal

### 1.3 Response Format

**Standard Success Response:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "id": 1,
    "email": "user@example.com"
  },
  "timestamp": "2026-04-09T10:30:00Z"
}
```

**Standard Error Response:**
```json
{
  "status": "error",
  "code": 400,
  "error": {
    "message": "Invalid donation amount",
    "field": "amount",
    "details": "Amount must be greater than 0"
  },
  "timestamp": "2026-04-09T10:30:00Z"
}
```

---

## 2. Authentication

### 2.1 Authentication Methods

**Session Authentication (Default):**
- Used for web browsers
- Session cookie set after login
- Automatic CSRF protection

**Token Authentication (API Clients):**
- Bearer token in Authorization header
- Token format: `Authorization: Bearer <token>`
- 30-day expiration

### 2.2 Login Endpoint

```
POST /auth/login/
Content-Type: application/json

Request Body:
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

Response (200 OK):
{
  "status": "success",
  "data": {
    "user_id": 1,
    "email": "user@example.com",
    "token": "abc123..."
  }
}
```

### 2.3 Logout Endpoint

```
POST /auth/logout/
Authorization: Bearer <token>

Response (200 OK):
{
  "status": "success",
  "message": "Logged out successfully"
}
```

### 2.4 Password Reset

```
POST /auth/password-reset/
Content-Type: application/json

Request:
{
  "email": "user@example.com"
}

Response (200 OK):
{
  "status": "success",
  "message": "Password reset email sent"
}
```

---

## 3. ENDPOINTS

### 3.1 Users Endpoints

#### List Current User

```
GET /users/me/
Authorization: Bearer <token>

Response (200 OK):
{
  "status": "success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2026-01-15T10:00:00Z",
    "is_active": true
  }
}
```

#### Update User Profile

```
PATCH /users/me/
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "first_name": "John",
  "last_name": "Doe"
}

Response (200 OK):
{
  "status": "success",
  "data": { /* updated user */ }
}
```

#### Change Password

```
POST /users/me/change-password/
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}

Response (200 OK):
{
  "status": "success",
  "message": "Password changed successfully"
}
```

---

### 3.2 Donations Endpoints

#### List Donations (User's Own)

```
GET /donations/
Authorization: Bearer <token>

Query Parameters:
- page: Pagination page (default: 1)
- search: Search by donor name
- status: Filter by status (completed, pending, failed)
- date_from: ISO date format
- date_to: ISO date format

Response (200 OK):
{
  "status": "success",
  "data": {
    "count": 25,
    "next": "https://api.dc48k.org/api/v1/donations/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "donor_name": "John Smith",
        "amount": "100.00",
        "currency": "USD",
        "status": "completed",
        "message": "Great cause!",
        "created_at": "2026-04-01T10:00:00Z"
      }
    ]
  }
}
```

#### Create Donation (Anonymous)

```
POST /donations/
Content-Type: application/json

Request:
{
  "amount": "50.00",
  "donor_name": "Anonymous",
  "donor_email": "donor@example.com",
  "message": "Supporting your mission"
}

Response (201 Created):
{
  "status": "success",
  "data": {
    "id": 2,
    "amount": "50.00",
    "status": "completed",
    "receipt_url": "https://dc48k.org/receipts/2.pdf"
  }
}
```

#### Create Donation (Authenticated)

```
POST /donations/
Authorization: Bearer <token>
Content-Type: application/json

Request:
{
  "amount": "100.00",
  "message": "Monthly support"
}

Response (201 Created):
{
  "status": "success",
  "data": { /* donation object */ }
}
```

#### Get Donation Detail

```
GET /donations/{id}/
Authorization: Bearer <token>

Response (200 OK):
{
  "status": "success",
  "data": {
    "id": 1,
    "amount": "100.00",
    "status": "completed",
    "created_at": "2026-04-01T10:00:00Z",
    "receipt_sent": true
  }
}
```

#### Update Donation (Admin Only)

```
PATCH /donations/{id}/
Authorization: Bearer <admin_token>
Content-Type: application/json

Request:
{
  "status": "refunded"
}

Response (200 OK):
{
  "status": "success",
  "data": { /* updated donation */ }
}
```

#### Delete Donation (Admin Only)

```
DELETE /donations/{id}/
Authorization: Bearer <admin_token>

Response (204 No Content):
```

---

### 3.3 Support Tickets Endpoints

#### List Support Tickets

```
GET /support/tickets/
Authorization: Bearer <token>

Query Parameters:
- status: Filter by status
- priority: Filter by priority
- search: Search title/description

Response (200 OK):
{
  "status": "success",
  "data": {
    "count": 5,
    "results": [
      {
        "id": 1,
        "subject": "Cannot update donation",
        "status": "open",
        "priority": "medium",
        "created_at": "2026-04-09T10:00:00Z",
        "assigned_to": "staff@dc48k.org"
      }
    ]
  }
}
```

#### Create Support Ticket

```
POST /support/tickets/
Content-Type: application/json

Request:
{
  "subject": "Issue with donation",
  "description": "I was charged twice for my donation",
  "priority": "high"
}

Response (201 Created):
{
  "status": "success",
  "data": {
    "id": 1,
    "reference": "TKT-2026-00001",
    "status": "open"
  }
}
```

#### Get Ticket Detail

```
GET /support/tickets/{id}/
Authorization: Bearer <token>

Response (200 OK):
{
  "status": "success",
  "data": {
    "id": 1,
    "subject": "Issue with donation",
    "description": "...",
    "responses": [
      {
        "id": 1,
        "responder": "support@dc48k.org",
        "response_text": "We're investigating this...",
        "created_at": "2026-04-09T11:00:00Z"
      }
    ]
  }
}
```

#### Add Ticket Response (Staff)

```
POST /support/tickets/{id}/responses/
Authorization: Bearer <staff_token>
Content-Type: application/json

Request:
{
  "response_text": "We have resolved this issue..."
}

Response (201 Created):
{
  "status": "success",
  "data": { /* response object */ }
}
```

#### Update Ticket (Staff)

```
PATCH /support/tickets/{id}/
Authorization: Bearer <staff_token>
Content-Type: application/json

Request:
{
  "status": "resolved"
}

Response (200 OK):
{
  "status": "success",
  "data": { /* updated ticket */ }
}
```

---

### 3.4 News/Articles Endpoints

#### List Articles

```
GET /news/articles/
Query Parameters:
- category: Filter by category
- search: Search title/body
- page: Pagination

Response (200 OK):
{
  "status": "success",
  "data": {
    "results": [
      {
        "id": 1,
        "title": "Impact Report 2025",
        "slug": "impact-report-2025",
        "category": "news",
        "published_at": "2026-04-01T10:00:00Z",
        "view_count": 250
      }
    ]
  }
}
```

#### Get Article Detail

```
GET /news/articles/{slug}/

Response (200 OK):
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Impact Report 2025",
    "body": "Long article content...",
    "author": "admin@dc48k.org",
    "published_at": "2026-04-01T10:00:00Z"
  }
}
```

#### Create Article (Staff)

```
POST /news/articles/
Authorization: Bearer <staff_token>
Content-Type: application/json

Request:
{
  "title": "New Initiative Launch",
  "body": "We are pleased to announce...",
  "category": "news",
  "is_published": true
}

Response (201 Created):
{
  "status": "success",
  "data": { /* article object */ }
}
```

---

### 3.5 Crisis/Help Endpoints

#### Get Crisis Resources

```
GET /support/crisis/

Response (200 OK):
{
  "status": "success",
  "data": {
    "crisis_hotline": "+1-800-XXX-XXXX",
    "text_number": "XXXXX",
    "resources": [
      {
        "name": "Local Crisis Hotline",
        "number": "+1-XXX-XXX-XXXX",
        "hours": "24/7"
      }
    ]
  }
}
```

#### Get Help FAQ

```
GET /support/faq/
Query Parameters:
- category: Filter by category
- search: Search questions

Response (200 OK):
{
  "status": "success",
  "data": {
    "results": [
      {
        "id": 1,
        "question": "How do I donate?",
        "answer": "You can donate by...",
        "category": "donations"
      }
    ]
  }
}
```

---

### 3.6 Alert Subscription Endpoints

#### List Alert Subscriptions

```
GET /alerts/subscriptions/
Authorization: Bearer <token>

Response (200 OK):
{
  "status": "success",
  "data": {
    "results": [
      {
        "id": 1,
        "email": "user@example.com",
        "alert_type": "news",
        "is_active": true
      }
    ]
  }
}
```

#### Create Alert Subscription

```
POST /alerts/subscriptions/
Content-Type: application/json

Request:
{
  "email": "user@example.com",
  "alert_type": "news"
}

Response (201 Created):
{
  "status": "success",
  "data": { /* subscription object */ }
}
```

#### Unsubscribe (One-Click)

```
GET /alerts/unsubscribe/{token}/

Response (200 OK):
{
  "status": "success",
  "message": "Unsubscribed successfully"
}
```

---

## 4. Error Handling

### 4.1 HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful retrieval |
| 201 | Created | Resource created |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate email/unique constraint |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Unexpected error |
| 503 | Service Unavailable | Maintenance mode |

### 4.2 Error Response Format

```json
{
  "status": "error",
  "code": 400,
  "error": {
    "message": "Validation failed",
    "errors": [
      {
        "field": "amount",
        "message": "Amount must be greater than 0"
      }
    ]
  }
}
```

### 4.3 Common Errors

**Invalid Amount:**
```json
{
  "error": {
    "message": "Invalid donation amount",
    "field": "amount",
    "constraint": "min_value=1"
  }
}
```

**Duplicate Email:**
```json
{
  "error": {
    "message": "Email already registered",
    "field": "email"
  }
}
```

**Authentication Failed:**
```json
{
  "error": {
    "message": "Invalid credentials",
    "code": "INVALID_CREDENTIALS"
  }
}
```

---

## 5. Rate Limiting

### 5.1 Rate Limit Headers

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1712671800
```

### 5.2 Rate Limit Tiers

| User Type | Requests/Minute | Burst |
|-----------|---|---|
| Anonymous | 20 | 5 |
| Authenticated | 100 | 20 |
| Premium | 500 | 100 |
| Admin | Unlimited | Unlimited |

---

## 6. Pagination

### 6.1 Cursor-Based Pagination

**Request:**
```
GET /donations/?cursor=cD0yMDI2LTA0LTA5IDA5OjMwOjAw
```

**Response:**
```json
{
  "count": 150,
  "next": "https://api.dc48k.org/api/v1/donations/?cursor=cD0yMDI2LTA0LTA4",
  "previous": "https://api.dc48k.org/api/v1/donations/?cursor=cD0yMDI2LTA0LTEw",
  "results": [ /* items */ ]
}
```

### 6.2 Page Size

- Default: 20
- Maximum: 100
- Customizable via `?page_size=50`

---

## 7. Versioning & Deprecation

### 7.1 API Lifecycle

**Stable** → **Deprecated** (6 months) → **Removed**

### 7.2 Deprecation Example

**Deprecated Endpoint:**
```
GET /donations/ (v1)
```

**Replacement:**
```
GET /donations/ (v2)
```

**Headers in Response:**
```
Deprecation: true
Sunset: Wed, 09 Oct 2026 14:00:00 GMT
Link: </api/v2/donations/>; rel="successor-version"
```

---

## 8. Security Best Practices

- Always use HTTPS/TLS
- Include CSRF tokens in non-GET requests
- Sanitize and validate all inputs
- Never log sensitive data (passwords, tokens)
- Use strong password requirements
- Implement rate limiting
- Monitor suspicious activities

---

**Document Version:** 1.0  
**API Version:** v1 (Production)  
**Last Updated:** April 9, 2026  
**Next Review:** Quarterly
