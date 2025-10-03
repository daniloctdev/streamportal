# StreamPortal API

A secure FastAPI backend for searching movies and series with streaming availability checking.

## 🔒 Security Features

- **Environment Variables**: API keys stored securely in environment variables
- **CORS Protection**: Configurable CORS middleware for frontend integration
- **Input Validation**: Pydantic models for request validation
- **Error Handling**: Proper HTTP status codes and error messages
- **No Client-Side API Keys**: API keys never exposed to frontend
- **Rate Limiting**: Built-in rate limiting (60 requests/minute per IP)
- **Request Logging**: Comprehensive request/response logging

## 📊 Logging & Monitoring

### Structured Logging System

The API includes a comprehensive logging system with:

- **JSON Structured Logs**: Machine-readable log format for production
- **Console Output**: All logs output to console/stdout
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Request Tracking**: Full request/response logging with timing
- **Performance Monitoring**: Response time tracking

### Log Format

```json
{
  "timestamp": "2023-12-01T10:30:45.123456",
  "level": "INFO",
  "logger": "streamportal.main",
  "message": "Search request: Movie - 'Avengers'",
  "module": "main",
  "function": "search",
  "line": 45,
  "extra_fields": {
    "content_type": "Movie",
    "search_query": "Avengers",
    "language": "en-US"
  }
}
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/streamportal.git
cd streamportal
```

### 2. Environment Setup

Copy the environment template:
```bash
cp env.example .env
```

Edit `.env` with your configuration:
```bash
# Required: Get from https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_tmdb_api_key_here

# Optional: CORS origins (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional: Logging level
LOG_LEVEL=INFO
```

### 3. Install Dependencies with Poetry

```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 4. Run the Server

```bash
# Development
poetry run uvicorn app.main:app --reload

# Production
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3005
```

### 5. Access Documentation
- API Docs: `http://localhost:3005/docs`
- Health Check: `http://localhost:3005/health`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d
```

### Using Docker directly

```bash
# Build the image
docker build -t streamportal .

# Run with environment variables
docker run -p 3005:3005 \
  -e TMDB_API_KEY=your_actual_api_key_here \
  -e ALLOWED_ORIGINS=http://localhost:3000 \
  streamportal
```

## 📡 API Endpoints

### 1. Search Endpoint (`POST /search`)

Quick search that returns basic information without checking streaming availability.

**Request Body:**
```json
{
    "text_search": "string",
    "type_of_content": "Movie" | "Series",
    "option_language": "en-US"  // Optional, defaults to "en-US"
}
```

**Response:**
```json
{
    "results": [
        {
            "id": 123,
            "original_title": "Movie Title",
            "overview": "Movie description...",
            "release_date": "2023-01-01",
            "vote_average": 8.5,
            "poster": "https://image.tmdb.org/t/p/w500/poster.jpg"
        }
    ]
}
```

### 2. Details Endpoint (`POST /details`)

Get detailed information for a specific movie or series, including streaming availability check.

**Request Body:**
```json
{
    "content_id": 123,
    "type_of_content": "Movie" | "Series",
    "option_language": "en-US"  // Optional, defaults to "en-US"
}
```

**Movie Response:**
```json
{
    "details": {
        "id": 123,
        "url": "https://vixsrc.to/movie/123",
        "is_available": true,
        "original_title": "Movie Title",
        "overview": "Movie description...",
        "release_date": "2023-01-01",
        "vote_average": 8.5,
        "vote_count": 1000,
        "runtime": 120,
        "genres": ["Action", "Drama"],
        "poster": "https://image.tmdb.org/t/p/w500/poster.jpg",
        "backdrop_path": "https://image.tmdb.org/t/p/original/backdrop.jpg",
        "budget": 50000000,
        "revenue": 200000000,
        "status": "Released"
    }
}
```

**Series Response Sample:**
```json
{
    "details": {
        "id": 456,
        "name": "Series Name",
        "air_date": "2023-01-01",
        "vote_avg": 8.5,
        "overview": "Series description...",
        "poster": "https://image.tmdb.org/t/p/w500/poster.jpg",
        "is_available": true,
        "valid_seasons": [1, 2, 3],
        "valid_episodes": {
            "1": [1, 2, 3, 4, 5],
            "2": [1, 2, 3, 4, 5, 6],
            "3": [1, 2, 3]
        },
        "streaming_urls": [
            "https://vixsrc.to/tv/456/1/1",
            "https://vixsrc.to/tv/456/1/2"
        ],
        "number_of_seasons": 3,
        "number_of_episodes": 14,
        "status": "Returning Series",
        "genres": ["Drama", "Thriller"],
        "backdrop_path": "https://image.tmdb.org/t/p/original/backdrop.jpg",
        "first_air_date": "2023-01-01",
        "last_air_date": "2023-12-01",
        "vote_count": 1000,
        "popularity": 85.5
    }
}
```

## 🛡️ Error Management

### Structured Error Responses

All errors return consistent, structured responses:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Search query cannot be empty",
        "status_code": 400,
        "details": {
            "field": "text_search"
        }
    }
}
```

### Error Types

- **VALIDATION_ERROR** (400): Invalid input data
- **AUTHENTICATION_ERROR** (401): API key issues
- **NOT_FOUND_ERROR** (404): Resource not found
- **RATE_LIMIT_ERROR** (429): Rate limit exceeded
- **EXTERNAL_API_ERROR** (502): External API issues
- **STREAMING_AVAILABILITY_ERROR** (503): Streaming service issues
- **INTERNAL_ERROR** (500): Unexpected server errors

### Error Logging

All errors are automatically logged with:
- Error type and message
- Request details (IP, path, method)
- Stack traces for debugging
- Contextual information

## 🌐 Frontend Integration

### CORS Configuration

The API includes CORS middleware configured for common frontend frameworks:

- **React**: `http://localhost:3000`
- **Vue**: `http://localhost:8080`
- **Angular**: `http://localhost:4200`

Add your production domain to `ALLOWED_ORIGINS` in `.env`.

### Example Frontend Usage

```javascript
// 1. Search for movies
const searchResults = await fetch('http://localhost:3005/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        text_search: "Avengers",
        type_of_content: "Movie",
        option_language: "en-US"
    })
});

const { results } = await searchResults.json();

// 2. Get details when user clicks
const details = await fetch('http://localhost:3005/details', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        content_id: 123,
        type_of_content: "Movie",
        option_language: "en-US"
    })
});

const { details: movieDetails } = await details.json();
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `TMDB_API_KEY` | ✅ | TMDB API key | - |
| `ALLOWED_ORIGINS` | ❌ | CORS origins (comma-separated) | `http://localhost:3000` |
| `LOG_LEVEL` | ❌ | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `HOST` | ❌ | Server host | `0.0.0.0` |
| `PORT` | ❌ | Server port | `3005` |

### Production Deployment

1. **Set Environment Variables**:
   ```bash
   export TMDB_API_KEY=your_production_key
   export ALLOWED_ORIGINS=https://yourdomain.com
   export LOG_LEVEL=INFO
   ```

2. **Use Production Server**:
   ```bash
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 3005
   ```

3. **Behind Reverse Proxy** (recommended):
   ```nginx
   location /api/ {
       proxy_pass http://localhost:3005/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }
   ```

## 📊 Monitoring & Observability

### Health Check

Monitor API health:
```bash
curl http://localhost:3005/health
```

### Log Monitoring

Monitor logs in real-time:
```bash
# View logs in real-time
poetry run uvicorn app.main:app --reload 2>&1 | grep "INFO"

# Filter for specific operations
poetry run uvicorn app.main:app --reload 2>&1 | grep "Search request"

# Monitor errors
poetry run uvicorn app.main:app --reload 2>&1 | grep "ERROR"
```

### Performance Metrics

The API provides:
- **Response Time Headers**: `X-Process-Time` header on all responses
- **Request Logging**: All requests logged with timing
- **Error Tracking**: Detailed error logging with context
- **Rate Limit Monitoring**: Rate limit violations logged

## 🛡️ Security Best Practices

### ✅ What's Implemented

- **Environment Variables**: API keys never in code
- **CORS Protection**: Prevents unauthorized cross-origin requests
- **Input Validation**: All requests validated with Pydantic
- **Error Handling**: Proper HTTP status codes
- **No Client Secrets**: API keys never exposed to frontend
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Request Logging**: Full audit trail for security monitoring
- **Input Sanitization**: Removes potentially dangerous characters

### 🔒 Additional Recommendations

1. **Rate Limiting**: Already implemented (60 req/min per IP)
2. **Authentication**: Add JWT authentication for user-specific features
3. **HTTPS**: Always use HTTPS in production
4. **API Versioning**: Consider versioning for future updates
5. **Logging**: Structured logging already implemented
6. **Health Checks**: Use `/health` endpoint for monitoring

### 🚨 Security Checklist

- [ ] TMDB API key in environment variables
- [ ] CORS origins configured for your domains
- [ ] HTTPS enabled in production
- [ ] Rate limiting active (default: 60 req/min)
- [ ] Error messages don't expose sensitive information
- [ ] Regular security updates
- [ ] Log monitoring for suspicious activity

## 📊 Performance Benefits

- **Fast Search**: ~2-3 seconds (vs 10-15 seconds before)
- **On-Demand Details**: Only check streaming when needed
- **Reduced API Calls**: Optimized for webapp usage
- **Mobile Friendly**: Smaller payloads for mobile users
- **Concurrent Processing**: Async operations for better performance

## 🧪 Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_main.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Type checking
poetry run mypy .

# Linting
poetry run flake8 .
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run all hooks
poetry run pre-commit run --all-files
```

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**: Check `ALLOWED_ORIGINS` in `.env`
2. **API Key Errors**: Verify `TMDB_API_KEY` is set
3. **Import Errors**: Run `poetry install`
4. **Rate Limit Errors**: Check logs for rate limit violations

### Debug Mode

For development, you can enable debug mode:
```bash
export LOG_LEVEL=DEBUG
poetry run uvicorn app.main:app --reload --log-level debug
```

### Log Monitoring

```bash
# View all logs in real-time
poetry run uvicorn app.main:app --reload 2>&1 | tee app.log

# Filter for specific log levels
poetry run uvicorn app.main:app --reload 2>&1 | grep "ERROR"

# Monitor API performance
poetry run uvicorn app.main:app --reload 2>&1 | grep "response_time"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `poetry run pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [The Movie Database (TMDB)](https://www.themoviedb.org/) for providing the movie and series data
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [Uvicorn](https://www.uvicorn.org/) for the ASGI server
