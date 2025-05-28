# FastAPI Application

A modern FastAPI application with a well-structured architecture.

## Project Structure

```
├── api/                # API endpoints and routes
│   ├── routers/       # API route handlers
│   └── repository/    # Database repository layer
├── core/              # Core application components
│   ├── config/        # Configuration settings
│   ├── security/      # Security related code
│   └── domain/        # Domain models and business logic
├── db/                # Database related code
├── models/            # Database models
├── schemas/           # Pydantic schemas
├── services/          # Business logic services
├── tests/             # Test files
├── Dockerfile         # Docker configuration
├── compose.yaml       # Docker Compose configuration
└── requirements.txt   # Project dependencies
```

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Development Mode
```bash
uvicorn main:app --reload
```

### Using Docker
```bash
docker-compose up --build
```

## API Documentation

Once the application is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run tests using pytest:
```bash
pytest
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Run tests
4. Submit a pull request

## License

[Add your license here] 