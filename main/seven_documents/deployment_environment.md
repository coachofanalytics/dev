# Deployment & Environment Document – DC48K Support Platform

## Document Metadata

| Field | Value |
|-------|-------|
| **Title** | DC48K Support Platform – Deployment & Environment |
| **Author** |Serge Shema|
| **Date** | April 9, 2026 |
| **Version** | v1.0 |
| **Deployment Lead** | Infrastructure Engineer |

---

## 1. Environment Architecture

### 1.1 Environment Overview

```
     ┌─────────────────────────────────────────────────┐
     │          DC48K Deployment Architecture          │
     └─────────────────────────────────────────────────┘
     
     Developer Local → Git Push → GitHub → CI/CD Pipeline
                                            ↓
                ┌───────────────────────────┼───────────────────────────┐
                ↓                           ↓                           ↓
            Staging                    Production              Backup/Disaster
          (Heroku/AWS)                (Heroku/AWS)           Recovery (S3)
            ├─ Web Servers            ├─ Web Servers
            ├─ Database               ├─ Load Balancer
            ├─ Cache                  ├─ Database (Primary)
            └─ CDN                     ├─ Database (Replica)
                                       ├─ Cache Cluster
                                       ├─ CDN
                                       └─ Monitoring
```

### 1.2 Environment Tiers

| Tier | Purpose | URL | Scale |
|------|---------|-----|-------|
| **Development** | Local dev | localhost:8000 | 1 instance |
| **Staging** | Pre-production testing | staging.dc48k.org | 2 instances |
| **Production** | Live user environment | dc48k.org | 4+ instances |
| **DR** | Disaster recovery | dr.dc48k.org | Standby |

---

## 2. Development Environment

### 2.1 Local Setup

**Prerequisites:**
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+
- Git
- Docker (optional)

**Installation Steps:**

```bash
# Clone repository
git clone https://github.com/dcorg/dc48k.git
cd dc48k

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup database
python manage.py migrate
python manage.py createsuperuser

# Create .env file
cp .env.example .env

# Load example data
python manage.py loaddata initial_data

# Run development server
python manage.py runserver

# In another terminal: run Celery
celery -A coda_project worker -l info
```

### 2.2 .env Configuration (Local)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-dev
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dc48k_dev
POSTGRES_USER=dev_user
POSTGRES_PASSWORD=dev_password
POSTGRES_DB=dc48k_dev

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_URL=redis://localhost:6379/1

# Email (Console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# AWS (S3)
AWS_ACCESS_KEY_ID=dev_key
AWS_SECRET_ACCESS_KEY=dev_secret
AWS_STORAGE_BUCKET_NAME=dc48k-dev

# Logging
LOG_LEVEL=DEBUG

# Feature flags
DEBUG_TOOLBAR=True
USE_SILK=True
```

### 2.3 Docker Development (Optional)

**docker-compose.yml (Development):**

```yaml
version: '3.8'

services:
  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: dc48k_dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://dev_user:dev_password@db:5432/dc48k_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A coda_project worker -l info
    volumes:
      - .:/app
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://dev_user:dev_password@db:5432/dc48k_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

**Start Development Stack:**
```bash
docker-compose up
# Access app at http://localhost:8000
```

---

## 3. Staging Environment

### 3.1 Staging Deployment

**Platform:** Heroku (or AWS EC2)  
**Tier:** Standard-2x  
**Database:** PostgreSQL Standard (staging)

**Deployment Process:**

```bash
# Configure Heroku remote
heroku create dc48k-staging --remote staging

# Add PostgreSQL
heroku addons:create heroku-postgresql:standard-0 --remote staging

# Add Redis
heroku addons:create heroku-redis:premium-0 --remote staging

# Set config variables
heroku config:set DEBUG=False --remote staging
heroku config:set SECRET_KEY=your-staging-key --remote staging

# Deploy
git push staging main

# Run migrations
heroku run python manage.py migrate --remote staging

# Create superuser
heroku run python manage.py createsuperuser --remote staging
```

### 3.2 Staging .env Configuration

```env
# Django
DEBUG=False
SECRET_KEY=${SECRET_KEY_STAGING}
ALLOWED_HOSTS=staging.dc48k.org
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Database
DATABASE_URL=postgresql://...@staging-db.herokuapp.com:5432/dc48k_staging

# Redis
REDIS_URL=redis://...staging.redis:6379/0

# Email (SendGrid)
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=${SENDGRID_API_KEY}

# AWS S3
AWS_STORAGE_BUCKET_NAME=dc48k-staging
AWS_S3_REGION_NAME=us-east-1

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=${SENTRY_DSN_STAGING}

# Security
CORS_ALLOWED_ORIGINS=https://staging.dc48k.org
```

### 3.3 Staging Testing Checklist

Before promoting to production:

- [ ] All tests passing (100%)
- [ ] Performance acceptable (<500ms p95)
- [ ] Database backup tested
- [ ] Email notifications working
- [ ] File uploads functional
- [ ] Payment gateway functioning (sandbox)
- [ ] Monitoring alerts active
- [ ] Log aggregation working
- [ ] Backup systems verified

---

## 4. Production Environment

### 4.1 Production Architecture

**Platform:** AWS / Heroku Pro  
**Load Balancer:** AWS ALB (Application Load Balancer)  
**Database:** RDS PostgreSQL (Multi-AZ)  
**Caching:** AWS ElastiCache (Redis Cluster)  
**Static Files:** CloudFront + S3  
**Email:** SendGrid

```
Internet
  ↓
Route 53 (DNS)
  ↓
AWS ALB (443)
  ↓
    ┌─────────────────────┬─────────────────────┬─────────────────────┐
    ↓                     ↓                     ↓
 App Server 1        App Server 2         App Server 3
(EC2 t3.large)      (EC2 t3.large)       (EC2 t3.large)
 [Gunicorn]          [Gunicorn]           [Gunicorn]
    ↓                     ↓                     ↓
    └─────────────────────┬─────────────────────┘
                          ↓
                    RDS Multi-AZ
                   (Primary/Replica)
                          ↓
    ┌─────────────────────┼─────────────────────┐
    ↓                     ↓                     ↓
ElastiCache         S3 Bucket          CloudFront CDN
(Redis Cluster)    (Static Files)      (Caching Layer)
```

### 4.2 Production Deployment

**Release Process:**

```bash
# 1. Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 2. Build process (automated via GitHub Actions)
# - Run tests
# - Create deployment package
# - Push to ECR (if using Docker)

# 3. Deploy to staging first
aws elasticbeanstalk create-environment-resources \
  --environment-name dc48k-staging

# 4. Run final verification
./scripts/smoke_tests.sh https://staging.dc48k.org

# 5. Deploy to production (blue-green)
aws elasticbeanstalk update-environment \
  --environment-name dc48k-prod \
  --version-label v1.0.0

# 6. Monitor deployment
aws elasticbeanstalk describe-environment-health \
  --environment-name dc48k-prod

# 7. Validate in production
./scripts/smoke_tests.sh https://dc48k.org

# 8. Monitor for 30 minutes
# Check error rates, response times, logger
```

### 4.3 Production .env Configuration

```env
# Django
DEBUG=False
SECRET_KEY=${SECRET_KEY_PROD}  # From AWS Secrets Manager
ALLOWED_HOSTS=
dc48k.org,www.dc48k.org,api.dc48k.org
ENVIRONMENT=production

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True

# Database
DATABASE_URL=postgresql://rds-prod.amazonaws.com:5432/dc48k_prod
DB_BACKUP_SCHEDULE=daily-2am
DB_BACKUP_RETENTION=30  # days

# Redis/Cache
REDIS_URL=redis://elasticache-prod.amazonaws.com:6379/0
CACHE_TIMEOUT=3600

# Email (Production)
EMAIL_BACKEND=sendgrid_backend.SendgridBackend
SENDGRID_API_KEY=${SENDGRID_API_KEY_PROD}
DEFAULT_FROM_EMAIL=noreply@dc48k.org

# AWS S3
AWS_STORAGE_BUCKET_NAME=dc48k-prod
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=cdn.dc48k.org
AWS_CLOUDFRONT_DISTRIBUTION_ID=${CF_DIST_ID}

# Logging & Monitoring
SENTRY_DSN=${SENTRY_DSN_PROD}
LOG_LEVEL=WARNING
DATADOG_API_KEY=${DATADOG_API_KEY}
NEWRELIC_LICENSE_KEY=${NR_LICENSE_KEY}

# Rate limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600  # 1 hour

# Backup/DR
BACKUPS_ENABLED=True
BACKUP_DESTINATION=s3://dc48k-backups-prod/
```

### 4.4 Auto-Scaling Configuration

**Scaling Policy:**

```yaml
# AWS Auto Scaling Group
Min Capacity: 3 instances
Max Capacity: 10 instances
Target Capacity: 5 instances

Scaling Triggers:
- CPU Utilization > 70% → Scale up
- CPU Utilization < 30% → Scale down (cooldown: 5 min)
- Memory > 80% → Alert immediately
- Response Time p95 > 1000ms → Scale up

Scaling Actions:
- Add/Remove 2 instances per action
- Cooldown: 3 minutes between scaling events
- Drain time: 60 seconds before termination
```

---

## 5. Infrastructure as Code

### 5.1 Terraform Configuration (AWS)

**main.tf - Infrastructure:**

```hcl
# Provider
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "dc48k-vpc"
    Environment = var.environment
  }
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier     = "dc48k-${var.environment}-db"
  engine         = "postgres"
  engine_version = "14.7"
  instance_class = "db.t3.medium"
  allocated_storage = 100
  storage_encrypted = true
  
  db_name  = "dc48k_${var.environment}"
  username = var.db_user
  password = random_password.db_password.result
  
  multi_az               = var.environment == "production" ? true : false
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "02:00-03:00"
  maintenance_window     = "sun:03:00-sun:04:00"
  
  vpc_security_group_ids = [aws_security_group.db.id]
  
  tags = {
    Name        = "dc48k-${var.environment}-db"
    Environment = var.environment
  }
}

# ElastiCache (Redis)
resource "aws_elasticache_cluster" "main" {
  cluster_id           = "dc48k-${var.environment}-redis"
  engine               = "redis"
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_nodes
  parameter_group_name = "default.redis7"
  automatic_failover_enabled = var.environment == "production" ? true : false
  
  security_group_ids = [aws_security_group.redis.id]
  
  tags = {
    Name        = "dc48k-${var.environment}-redis"
    Environment = var.environment
  }
}

# ALB
resource "aws_lb" "main" {
  name               = "dc48k-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]

  enable_deletion_protection = var.environment == "production" ? true : false

  tags = {
    Name        = "dc48k-${var.environment}-alb"
    Environment = var.environment
  }
}
```

### 5.2 Terraform Variables

**variables.tf:**

```hcl
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be staging or production."
  }
}

variable "db_user" {
  description = "Database admin username"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 1
}
```

---

## 6. CI/CD Pipeline

### 6.1 GitHub Actions Workflow

**.github/workflows/deploy.yml:**

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14-alpine
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: dc48k_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache Python dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: python manage.py test

      - name: Check code quality
        run: |
          flake8 .
          black --check .

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: |
          docker build -t dc48k:${{ github.ref_name }} .
          docker tag dc48k:${{ github.ref_name }} dc48k:latest

      - name: Push to AWS ECR
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws ecr get-login-password --region us-east-1 | docker login \
            --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
          docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/dc48k:${{ github.ref_name }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://dc48k.org
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to AWS
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          aws elasticbeanstalk create-application-version \
            --application-name dc48k \
            --version-label ${{ github.ref_name }} \
            --source-bundle S3Bucket=dc48k-builds,S3Key=dc48k-${{ github.ref_name }}.zip

          aws elasticbeanstalk update-environment \
            --environment-name dc48k-prod \
            --version-label ${{ github.ref_name }}

      - name: Verify deployment
        run: |
          timeout 600 bash -c 'until curl -f https://dc48k.org/health; do sleep 10; done'
```

---

## 7. Monitoring & Logging

### 7.1 Monitoring Stack

**Tools:**
- **New Relic:** Application Performance Monitoring
- **Datadog:** Infrastructure & Log monitoring
- **CloudWatch:** AWS-native monitoring
- **Sentry:** Error tracking

**Key Metrics:**

```
Application:
- Request rate
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- DB query time
- Cache hit rate

Infrastructure:
- CPU utilization
- Memory usage
- Disk I/O
- Network I/O

Business:
- Donation volume
- User registrations
- Feature usage
- Conversion rates
```

### 7.2 Alerting Rules

| Alert | Condition | Action |
|-------|-----------|--------|
| High Error Rate | 5xx errors > 1% | Page oncall |
| Down Time | All servers down | Immediate escalation |
| DB Performance Degradation | Query time > 1s | Notify DBA |
| Disk Space Critical | Usage > 90% | Immediate alert |
| Memory Leak Detected | Memory growth > 20% | Investigation |
| Backup Failure | Backup status = failed | Review backup logs |

### 7.3 Logging Configuration

**Log Aggregation: ELK Stack (Elasticsearch, Logstash, Kibana)**

```python
# settings.py - Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(timestamp)s %(level)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'datadog': {
            'class': 'datadog.api.LogHandler',
            'api_key': settings.DATADOG_API_KEY,
            'level': 'WARNING',
        },
    },
    'root': {
        'handlers': ['console', 'datadog'],
        'level': 'INFO',
    },
}
```

---

## 8. Backup & Disaster Recovery

### 8.1 Backup Strategy

**Database Backups:**
- Frequency: Daily automated + hourly snapshots
- Retention: 30 days (production), 7 days (staging)
- Replication: Multi-region backup
- Test Frequency: Weekly restore test

**Storage Backups:**
- S3 versioning enabled
- Cross-region replication enabled
- Retention: 90 days for versions
- Lifecycle policy: Archive to Glacier after 30 days

### 8.2 Recovery Procedures

**RTO (Recovery Time Objective):** 2 hours  
**RPO (Recovery Point Objective):** 15 minutes

**DR Steps:**

```bash
# 1. Identify failure
# Monitors detect issue → Alert sent

# 2. Initiate failover
aws rds failover-db-cluster --db-cluster-identifier dc48k-prod

# 3. Promote replica database
aws rds promote-read-replica --db-instance-identifier dc48k-prod-replica

# 4. Update DNS/Load Balancer
aws route53 change-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --change-batch '{...}'

# 5. Verify application connectivity
curl https://dc48k.org/health

# 6. Monitor recovery
# Watch error rates and response times for 30 min
```

### 8.3 Disaster Recovery Runbook

**Database Corruption:**
```bash
# Option 1: Restore from automated backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier dc48k-prod-restored \
  --db-snapshot-identifier dc48k-prod-2025-04-09

# Option 2: Point-in-time recovery
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier dc48k-prod \
  --target-db-instance-identifier dc48k-prod-pitr \
  --restore-time 2025-04-09T10:00:00Z
```

---

## 9. Security Hardening

### 9.1 Network Security

**Security Groups:**
- Load Balancer: Allow HTTP (80), HTTPS (443) from internet
- Application: Allow port 8000 from ALB only
- Database: Allow port 5432 from Application layer only
- Cache: Allow port 6379 from Application layer only

**Network Architecture:**
- Public subnets: ALB, NAT Gateway
- Private subnets: Application servers, Database, Cache
- Bastion host for admin access

### 9.2 SSL/TLS Configuration

```nginx
# SSL/TLS
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# Headers
add_header Strict-Transport-Security "max-age=31536000" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### 9.3 Secrets Management

**AWS Secrets Manager:**
```bash
# Store secrets
aws secretsmanager create-secret \
  --name dc48k/prod/db-password \
  --secret-string "password123"

# Retrieve secrets (in app)
import boto3
client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='dc48k/prod/db-password')
secret = response['SecretString']
```

---

## 10. Deployment Checklist

### 10.1 Pre-Deployment

- [ ] All tests passing (100%)
- [ ] Code review approved
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Database migrations tested
- [ ] Static files collected
- [ ] Configuration validated
- [ ] Backup system verified
- [ ] Monitoring alerts active
- [ ] Runbook reviewed

### 10.2 Deployment Day

- [ ] Notify stakeholders
- [ ] Start monitoring dashboard
- [ ] Verify auto-scaling enabled
- [ ] Deploy to staging first
- [ ] Run smoke tests (staging)
- [ ] Deploy to production (blue-green)
- [ ] Monitor for 1 hour (all metrics)
- [ ] Run smoke tests (production)
- [ ] Verify data integrity
- [ ] On-call engineer available

### 10.3 Post-Deployment

- [ ] Monitor key metrics for 24 hours
- [ ] Review error logs
- [ ] Validate user reports
- [ ] Performance baseline recorded
- [ ] Document any issues
- [ ] Update runbooks
- [ ] Share deployment notes

---

## 11. Cost Optimization

### 11.1 Resource Sizing

| Component | Staging | Production |
|-----------|---------|------------|
| EC2 | t3.small (1) | t3.large (3+) |
| RDS | db.t3.small | db.t3.medium (Multi-AZ) |
| Redis | cache.t3.micro | cache.r6g.large |
| EBS | 50 GB | 500 GB |
| NAT Gateway | Shared | Dedicated |

### 11.2 Cost Monitoring

**AWS Budgets Alert:** >$1,500/month → notify  
**Reserved Instances:** 40% discount for 1-year commitment  
**Spot Instances:** Non-critical workloads (20% of compute capacity)

---

**Document Version:** 1.0  
**Deployment Platform:** AWS / Heroku  
**Infrastructure as Code:** Terraform  
**Container Registry:** AWS ECR  
**Last Updated:** April 9, 2026  
**Maintained By:** DevOps Team
