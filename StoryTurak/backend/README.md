# StoryTurak Backend

A modular FastAPI backend for the StoryTurak project.

## Structure

- `app/api/`: Endpoint handlers organized by feature.
- `app/core/`: Security and configuration.
- `app/db/`: Database connection and CRUD operations.
- `app/models/`: Pydantic schemas.
- `app/services/`: Business logic and background tasks.

## Running

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Documentation

The API documentation is available at `/docs` or `/redoc` when the server is running.
