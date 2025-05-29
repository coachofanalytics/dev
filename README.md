# FastAPI Application

A modern FastAPI application with a well-structured architecture, supporting both development and production environments.

## Project Structure

```
├── api/                # API endpoints and routes
│   ├── routers/       # API route handlers
│   └── repository/    # Database repository layer
├── core/              # Core application components
│   ├── config/        # Configuration settings
│   ├── security/      # Security related code
│   └── domain/        # Domain models and business logic
├── models/            # Database models
│   ├── accounts/      # User and authentication models
│   ├── management/    # Management related models
│   └── getdata/       # Data retrieval models
├── schemas/           # Pydantic schemas
├── services/          # Business logic services
├── tests/             # Test files
├── utils/             # Utility functions and scripts
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Development Docker Compose configuration
├── docker-compose.prod.yml # Production Docker Compose configuration
└── requirements.txt   # Project dependencies
```

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv311
   source .venv311/bin/activate  # On Windows: .venv311\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
## Review Requirement 
   Link: https://docs.google.com/spreadsheets/d/10qnLVTmqzWaspSpY49tfBVwIK__ylRzF4loUUJWuqPQ/edit?gid=0#gid=0
## Running the Application

### Development Environment (Docker)

The development environment uses a Docker container for both the application and database:

1. Start the development environment:
   ```bash
   docker compose up
   ```
   This will:
   - Start a PostgreSQL database on port 5433
   - Create necessary database tables
   - Start the FastAPI application on port 8002
   - Enable hot-reload for development

2. Access the application:
   - API: `http://localhost:8002`
   - Swagger UI: `http://localhost:8002/docs`
   - ReDoc: `http://localhost:8002/redoc`

### Production Environment (Local Database)

The production environment uses your local PostgreSQL database:

1. Start the production environment:
   ```bash
   docker compose -f docker-compose.prod.yml up
   ```
   This will:
   - Connect to your local PostgreSQL database on port 5432
   - Start the FastAPI application on port 8002
   - Run without hot-reload for better performance

## Database Management

### Development Database

The development database is automatically initialized with required tables. To reset the database:

```bash
docker compose down -v  # Removes the database volume
docker compose up      # Creates a fresh database
```

### Creating Test Users

To create a test user in the development database:

1. Connect to the database:
   ```bash
   docker compose exec db psql -U postgres -d CODA_DEV
   ```

2. Insert a test user:
   ```sql
   INSERT INTO public.accounts_customeruser (
       id, username, first_name, last_name, email, 
       is_admin, is_staff, is_client, is_applicant, email_verified
   ) VALUES (
       gen_random_uuid(), 'testuser', 'Test', 'User', 'test@example.com',
       true, true, true, false, true
   );
   ```

## Environment Variables

The application uses the following environment variables. Create a `.env` file with these variables:

```
# Database Configuration
DATABASE_URL=postgresql://<username>:<password>@db:5432/<database_name>  # Development
DATABASE_URL=postgresql://<username>:<password>@host.docker.internal:5432/<database_name>  # Production
DB_SCHEMA=public
POSTGRESDB_HOST=db  # or host.docker.internal for production
POSTGRES_DB_NAME=<database_name>
POSTGRESDB_USER=<username>
POSTGRESSPASS=<password>

# Application Configuration
SECRET_KEY=<your-secret-key>
ENVIRONMENT=development  # or production
DEBUG=True  # or False for production
```

## Testing

Run tests using pytest:
```bash
pytest
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests
4. Submit a pull request

## License

[Add your license here] 

## Docker Architecture

### Process Flow
```
docker-compose up
    │
    ├── 1. Reads docker-compose.yml
    │   ├── Finds service definitions (web, db)
    │   ├── Reads environment variables
    │   └── Sets up networks and volumes
    │
    ├── 2. Builds web service
    │   ├── Uses Dockerfile
    │   │   ├── Starts with Python 3.11 base image
    │   │   ├── Sets working directory to /app
    │   │   ├── Copies requirements.txt
    │   │   ├── Installs dependencies
    │   │   └── Copies application code
    │   └── Creates container
    │
    └── 3. Starts db service
        ├── Uses postgres:15 image
        ├── Sets up volumes for data persistence
        └── Configures environment variables
```

### Container Architecture
```
Docker Host
    │
    ├── Network: fastapi-network
    │   │
    │   ├── Container: app-web-1
    │   │   ├── Port: 8002:8002 (host:container)
    │   │   ├── Volume: .:/app (host:container)
    │   │   └── Environment: From .env file
    │   │
    │   └── Container: app-db-1
    │       ├── Port: 5434:5432 (host:container)
    │       └── Volume: postgres_data:/var/lib/postgresql/data
    │
    └── Volumes
        └── postgres_data (persistent database storage)
```

### Application Flow
```
app-web-1 Container
    │
    ├── 1. Starts uvicorn server
    │   ├── Loads environment variables
    │   ├── Connects to database
    │   └── Initializes FastAPI application
    │
    ├── 2. Database Connection
    │   ├── Uses DATABASE_URL from environment
    │   └── Connects to app-db-1 through Docker network
    │
    └── 3. API Endpoints
        ├── /users/ - Fetches users from database
        └── Other endpoints...
```

### Key Components
```
Dockerfile
    ├── Base Image: python:3.11
    ├── Dependencies: requirements.txt
    └── Application Code: /app

docker-compose.yml
    ├── Services
    │   ├── web
    │   │   ├── build: .
    │   │   ├── ports: "8002:8002"
    │   │   └── volumes: .:/app
    │   │
    │   └── db
    │       ├── image: postgres:15
    │       └── volumes: postgres_data:/var/lib/postgresql/data
    │
    └── Networks
        └── fastapi-network
```

### Data Flow
```
Client Request
    │
    ├── 1. HTTP Request to localhost:8002
    │   └── Routes to app-web-1 container
    │
    ├── 2. FastAPI Application
    │   ├── Processes request
    │   └── Makes database query
    │
    ├── 3. Database Query
    │   ├── Goes through Docker network
    │   └── Reaches app-db-1 container
    │
    └── 4. Response
        ├── Database returns data
        └── FastAPI sends HTTP response
```

### Development Workflow
```
Local Development
    │
    ├── 1. Code Changes
    │   └── Automatically reflected due to volume mount
    │
    ├── 2. Database Changes
    │   ├── Persisted in postgres_data volume
    │   └── Survives container restarts
    │
    └── 3. Environment Variables
        ├── Loaded from .env file
        └── Available to both containers
```

### When to Restart Containers

You don't need to restart containers for every code change due to the volume mount and hot-reload:

**No Restart Needed For:**
- Python code changes
- New API routes
- Business logic modifications
- Template/static file updates

**Restart Required For:**
- Dockerfile modifications
- docker-compose.yml changes
- New dependencies in requirements.txt
- Environment variable changes
- Database resets

This architecture provides:
- Isolation between services
- Easy development with hot-reloading
- Persistent database storage
- Network isolation
- Environment variable management
- Scalability (can add more services) 