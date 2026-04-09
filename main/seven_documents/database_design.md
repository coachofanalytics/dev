# Database Design Document – DC48K Support Platform

## Document Metadata

| Field | Value |
|-------|-------|
| **Title** | DC48K Support Platform – Database Design |
| **Author** | Serge Shema|
| **Date** | April 9, 2026 |
| **Version** | v1.0 |
| **Database System** | PostgreSQL 13+ |

---

## 1. Database Overview

### 1.1 Design Principles

- **Normalization:** 3NF (Third Normal Form) applied
- **Relationships:** Foreign keys enforce referential integrity
- **Constraints:** Data validation at database level
- **Indexing:** Strategic indexes on frequently queried columns
- **Performance:** Denormalization where necessary for common queries

### 1.2 Database Statistics

| Metric | Value |
|--------|-------|
| **Total Tables** | 12 |
| **Total Relationships** | 18 |
| **Indexes** | 25+ |
| **Constraints** | 30+ |
| **Stored Procedures** | 5 |

---

## 2. Entity Relationship Diagram (ERD)

### 2.1 ERD Description

```
Users (1) ──→ (Many) Donations
 ├─ id (PK)
 ├─ email (UNIQUE)
 ├─ password_hash
 ├─ is_active
 └─ created_at

Donations (Many) ──→ (1) Organizations
 ├─ id (PK)
 ├─ user_id (FK → Users)
 ├─ organization_id (FK)
 ├─ amount
 ├─ donor_name
 └─ status

Organizations (1) ──→ (Many) Donations
 ├─ id (PK)
 ├─ name
 ├─ description
 └─ logo_url

Donors (1) ──→ (Many) Donations
 ├─ id (PK)
 ├─ name
 ├─ email
 └─ phone

SupportTickets (Many) ──→ (1) Users
 ├─ id (PK)
 ├─ user_id (FK → Users)
 ├─ subject
 ├─ description
 ├─ status
 └─ priority

TicketResponses (Many) ──→ (1) SupportTickets
 ├─ id (PK)
 ├─ ticket_id (FK)
 ├─ responder_id (FK → Users)
 ├─ response_text
 └─ created_at

Articles (Many) ──→ (1) Users
 ├─ id (PK)
 ├─ author_id (FK → Users)
 ├─ title
 ├─ body
 ├─ category
 └─ published_at

AlertSubscriptions (Many) ──→ (1) Users
 ├─ id (PK)
 ├─ user_id (FK)
 ├─ email
 ├─ alert_type
 └─ is_active
```

---

## 3. Table Definitions & Models

### 3.1 User Table

**Model:** `auth_user` (Django default)

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| username | VARCHAR(150) | UNIQUE | Username |
| password | VARCHAR(255) | NOT NULL | Hashed password |
| first_name | VARCHAR(100) | | User's first name |
| last_name | VARCHAR(100) | | User's last name |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| is_staff | BOOLEAN | DEFAULT FALSE | Staff flag |
| is_superuser | BOOLEAN | DEFAULT FALSE | Admin flag |
| last_login | TIMESTAMP | | Last login timestamp |
| date_joined | TIMESTAMP | NOT NULL | Registration date |

**Indexes:**
- `idx_email` on email (UNIQUE)
- `idx_is_active` on is_active

**Constraints:**
- Email must be unique
- Password minimum 12 characters
- Must provide email for registration

---

### 3.2 Donation Table

**Model:** `Donation_organization`

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| user_id | BIGINT | FK → auth_user.id | Donor user |
| organization_id | BIGINT | FK → organizations.id | Organization |
| donor_name | VARCHAR(255) | | Anonymous donation name |
| donor_email | VARCHAR(255) | | Donor contact |
| amount | DECIMAL(10,2) | NOT NULL, CHECK >0 | Donation amount |
| currency | VARCHAR(3) | DEFAULT 'USD' | Currency code |
| status | VARCHAR(50) | DEFAULT 'completed' | Payment status |
| message | TEXT | | Donor message |
| receipt_sent | BOOLEAN | DEFAULT FALSE | Receipt email sent |
| created_at | TIMESTAMP | NOT NULL | Creation date |
| updated_at | TIMESTAMP | NOT NULL | Update date |

**Indexes:**
- `idx_user_id` on user_id (for donor lookup)
- `idx_organization_id` on organization_id
- `idx_created_at` on created_at (for reporting)
- `idx_status_created_at` composite on status, created_at

**Constraints:**
- Amount must be ≥ $1
- Status in ['pending', 'completed', 'failed', 'refunded']
- FK constraint with organizations table

---

### 3.3 Organization Table

**Model:** `Organization`

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| name | VARCHAR(255) | NOT NULL, UNIQUE | Organization name |
| slug | VARCHAR(255) | UNIQUE | URL-friendly name |
| description | TEXT | | Organization description |
| logo_url | VARCHAR(500) | | Logo image URL |
| website | VARCHAR(500) | | Organization website |
| email | VARCHAR(255) | | Contact email |
| phone | VARCHAR(20) | | Contact phone |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | NOT NULL | Creation date |

**Indexes:**
- `idx_slug` on slug (UNIQUE)
- `idx_is_active` on is_active

---

### 3.4 Donor Table

**Model:** `Donation_organisation` (alternate naming)

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| name | VARCHAR(255) | NOT NULL | Donor name |
| email | VARCHAR(255) | | Donor email |
| phone | VARCHAR(20) | | Donor phone |
| address | TEXT | | Mailing address |
| city | VARCHAR(100) | | City |
| state | VARCHAR(50) | | State/Province |
| zip_code | VARCHAR(20) | | Postal code |
| country | VARCHAR(100) | | Country |
| tax_id | VARCHAR(50) | | Tax identification |
| donation_count | INT | DEFAULT 0 | Total donations |
| total_donated | DECIMAL(12,2) | DEFAULT 0 | Cumulative donations |
| last_donation | TIMESTAMP | | Most recent donation |
| created_at | TIMESTAMP | NOT NULL | Creation date |

**Indexes:**
- `idx_email` on email
- `idx_total_donated` on total_donated (for reports)
- `idx_country` on country

---

### 3.5 Support Ticket Table

**Model:** `SupportTicket`

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| user_id | BIGINT | FK → auth_user.id | Ticket author |
| subject | VARCHAR(255) | NOT NULL | Ticket subject |
| description | TEXT | NOT NULL | Problem description |
| status | VARCHAR(50) | DEFAULT 'open' | Ticket status |
| priority | VARCHAR(50) | DEFAULT 'medium' | Priority level |
| category | VARCHAR(100) | | Support category |
| assigned_to | BIGINT | FK → auth_user.id | Assigned staff |
| created_at | TIMESTAMP | NOT NULL | Creation date |
| updated_at | TIMESTAMP | NOT NULL | Last update |
| resolved_at | TIMESTAMP | | Resolution date |

**Indexes:**
- `idx_user_id` on user_id
- `idx_status` on status
- `idx_priority_status` composite on priority, status
- `idx_created_at` on created_at

**Constraints:**
- Status in ['open', 'in_progress', 'resolved', 'closed']
- Priority in ['low', 'medium', 'high', 'urgent']

---

### 3.6 Ticket Response Table

**Model:** `TicketResponse`

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| ticket_id | BIGINT | FK → support_ticket.id | Parent ticket |
| responder_id | BIGINT | FK → auth_user.id | Staff member |
| response_text | TEXT | NOT NULL | Response content |
| is_internal | BOOLEAN | DEFAULT FALSE | Internal note |
| created_at | TIMESTAMP | NOT NULL | Creation date |

**Indexes:**
- `idx_ticket_id` on ticket_id
- `idx_responder_id` on responder_id

---

### 3.7 Article Table

**Model:** `Article`

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| author_id | BIGINT | FK → auth_user.id | Author |
| title | VARCHAR(255) | NOT NULL | Article title |
| slug | VARCHAR(255) | UNIQUE | URL slug |
| body | TEXT | NOT NULL | Article content |
| category | VARCHAR(100) | | Content category |
| is_published | BOOLEAN | DEFAULT FALSE | Published status |
| published_at | TIMESTAMP | | Publication date |
| view_count | INT | DEFAULT 0 | Popularity metric |
| created_at | TIMESTAMP | NOT NULL | Creation date |
| updated_at | TIMESTAMP | NOT NULL | Update date |

**Indexes:**
- `idx_slug` on slug
- `idx_is_published` on is_published
- `idx_published_at` on published_at
- `idx_view_count` on view_count

---

### 3.8 Alert Subscription Table

**Model:** `AlertSubscription`

| Column | Type | Constraints | Purpose |
|--------|------|-------------|---------|
| id | BIGINT | PK, AUTO_INCREMENT | Primary key |
| user_id | BIGINT | FK → auth_user.id | Subscriber |
| email | VARCHAR(255) | NOT NULL | Subscription email |
| alert_type | VARCHAR(100) | NOT NULL | Type of alerts |
| is_active | BOOLEAN | DEFAULT TRUE | Subscription status |
| unsubscribe_token | VARCHAR(100) | UNIQUE | One-click unsubscribe |
| created_at | TIMESTAMP | NOT NULL | Subscription date |
| updated_at | TIMESTAMP | NOT NULL | Last update |

**Indexes:**
- `idx_user_id` on user_id
- `idx_email_alert_type` composite on email, alert_type
- `idx_is_active` on is_active

**Constraints:**
- Email and alert_type must form unique pair
- Unsubscribe token must be cryptographically secure

---

## 4. Relationships & Constraints

### 4.1 Foreign Key Relationships

| Relationship | Constraint | Action |
|---|---|---|
| Donation.user_id → User.id | NOT NULL | CASCADE DELETE |
| Donation.organization_id → Organization.id | NOT NULL | RESTRICT |
| SupportTicket.user_id → User.id | NOT NULL | CASCADE DELETE |
| SupportTicket.assigned_to → User.id | NULLABLE | SET NULL |
| TicketResponse.ticket_id → SupportTicket.id | NOT NULL | CASCADE DELETE |
| TicketResponse.responder_id → User.id | NOT NULL | RESTRICT |
| Article.author_id → User.id | NOT NULL | SET NULL |
| AlertSubscription.user_id → User.id | NOT NULL | CASCADE DELETE |

### 4.2 Unique Constraints

- Email (User table) – One account per email
- Slug (Organization, Article tables) – URL uniqueness
- Tax ID (Donor table) – Tax identification uniqueness

### 4.3 Check Constraints

- Donation.amount > 0
- Donation.created_at ≤ Donation.updated_at
- SupportTicket.created_at ≤ SupportTicket.resolved_at

---

## 5. Indexing Strategy

### 5.1 Frequently Queried Indexes

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| Donation | user_id | B-tree | User donation history |
| Donation | status, created_at | Composite | Reporting queries |
| User | email_idx | Hash | Login operations |
| SupportTicket | status | B-tree | Dashboard filtering |
| Article | published_at | B-tree | News listing |
| AlertSubscription | is_active | B-tree | Active subscriber counts |

### 5.2 Index Maintenance

**Rebuild Strategy:**
- Automatic statistics update (VACUUM ANALYZE)
- Weekly manual REINDEX for production
- Remove unused indexes quarterly

**Monitoring:**
- Index bloat monitoring
- Query plan analysis
- Slow query logs

---

## 6. Data Integrity Constraints

### 6.1 Business Rules

1. **Donation Integrity:**
   - Amount must be positive
   - Status changes follow workflow (pending → completed or failed)
   - Receipt must be sent before marking as completed

2. **User Integrity:**
   - Email must be validated and unique
   - Password must meet complexity requirements
   - Active users can have multiple donations

3. **Support Integrity:**
   - Ticket must have valid initial status
   - Responses only allowed by assigned staff
   - Resolved tickets cannot accept new responses

---

## 7. Migration Strategy

### 7.1 Django Migrations

**Tool:** Django Migrations framework

**Process:**
1. Define model changes in `models.py`
2. Run `python manage.py makemigrations`
3. Review generated migration file
4. Test on development database
5. Run `python manage.py migrate` on all environments

### 7.2 Backward Compatibility

- New fields default to NULL or have default values
- Deprecated fields marked with deprecation warnings
- Zero-downtime migrations using multiple-step approach

### 7.3 Data Migration Examples

```python
# Migration: Add donor_name to Donation
from django.db import migrations, models

class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='donation_organization',
            name='donor_name',
            field=models.CharField(
                max_length=255, 
                null=True, 
                blank=True
            ),
        ),
    ]
```

---

## 8. Backup & Recovery

### 8.1 Backup Strategy

**Frequency:**
- Full backup: Daily (22:00 UTC)
- Incremental backup: Hourly
- Transaction log backup: Every 5 minutes

**Retention:**
- Daily backups: 7 days
- Weekly backups: 4 weeks
- Monthly backups: 12 months

**Storage:**
- Primary: On-site or AWS S3
- Secondary: Off-site geographically distant location
- Encrypted at rest and in transit

### 8.2 Recovery Procedures

**Recovery Time Objective (RTO):** <1 hour  
**Recovery Point Objective (RPO):** <15 minutes

**Point-in-Time Recovery:**
```sql
-- Restore to specific timestamp
pg_restore -d donation_db /backups/donation_db_2026-04-09.sql
```

---

## 9. Performance Tuning

### 9.1 Query Optimization

**N+1 Query Prevention:**
- Use `select_related()` for ForeignKey
- Use `prefetch_related()` for ManyToMany
- Limit SELECT fields with `.values()` or `.values_list()`

**Slow Query Identification:**
- Enable PostgreSQL slow query logging (>500ms)
- Use Django Debug Toolbar in development
- Parse query execution plans with `EXPLAIN ANALYZE`

### 9.2 Connection Pooling

**PgBouncer Configuration:**
- Pool mode: transaction
- Max connections: 500
- Reserve pool: 50

---

## 10. Database Security

### 10.1 Access Control

- Separate database users for app, admin, readonly
- Strongest privileges: least privilege principle
- Sensitive data: Column-level encryption where applicable

### 10.2 Encryption

- Passwords: PBKDF2 with salt
- Sensitive data: PostgreSQL pgcrypto extension
- In transit: SSL/TLS required

---

**Document Version:** 1.0  
**Database Version:** PostgreSQL 13+  
**Last Review:** April 9, 2026
