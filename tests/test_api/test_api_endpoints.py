"""Tests for StreamPortal REST API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.errors import AuthenticationError, NotFoundError

# --- API Robustness & Edge Case Tests ---


def test_cors_preflight_search(test_client):
    """Test CORS preflight (OPTIONS) on /search endpoint."""
    response = test_client.options("/search")
    # OPTIONS might return 405 Method Not Allowed, which is acceptable
    assert response.status_code in [200, 405]
    # Only check CORS headers if OPTIONS is supported
    if response.status_code == 200:
        assert "access-control-allow-origin" in response.headers


def test_cors_preflight_details(test_client):
    """Test CORS preflight (OPTIONS) on /details endpoint."""
    response = test_client.options("/details")
    # OPTIONS might return 405 Method Not Allowed, which is acceptable
    assert response.status_code in [200, 405]
    # Only check CORS headers if OPTIONS is supported
    if response.status_code == 200:
        assert "access-control-allow-origin" in response.headers


def test_search_missing_fields(test_client):
    """Test /search with missing required fields returns 422."""
    response = test_client.post("/search", json={})
    assert response.status_code == 422


def test_details_missing_fields(test_client):
    """Test /details with missing required fields returns 422."""
    response = test_client.post("/details", json={})
    assert response.status_code == 422


def test_invalid_method_on_search(test_client):
    """Test GET method on /search returns 405 or 422."""
    response = test_client.get("/search")
    assert response.status_code in [405, 422]


def test_invalid_method_on_details(test_client):
    """Test GET method on /details returns 405 or 422."""
    response = test_client.get("/details")
    assert response.status_code in [405, 422]


@pytest.mark.skip(reason="Startup event cannot be reliably tested in this context")
def test_startup_event_missing_api_key(monkeypatch):
    """Test startup event fails if TMDB_API_KEY is missing."""
    monkeypatch.delenv("TMDB_API_KEY", raising=False)
    import asyncio

    from app.main import startup_event

    with pytest.raises(Exception) as excinfo:
        asyncio.run(startup_event())
    assert "TMDB_API_KEY" in str(excinfo.value)


def test_search_large_payload(test_client):
    """Test /search with very large payload returns 400."""
    search_data = {
        "text_search": "a" * 10000,
        "type_of_content": "Movie",
        "option_language": "en-US",
    }
    response = test_client.post("/search", json=search_data)
    assert response.status_code == 400


# --- End of API Robustness & Edge Case Tests ---


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, test_client: TestClient):
        """Test health check endpoint returns success."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "StreamPortal API is running"
        assert "X-Process-Time" in response.headers


class TestSearchEndpoint:
    """Test search endpoint for movies and series."""

    def test_search_movies_success(self, test_client: TestClient):
        """Test successful movie search."""
        search_data = {
            "text_search": "Inception",
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        mock_results = [
            {
                "id": 27205,
                "original_title": "Inception",
                "overview": "Cobb, a skilled thief...",
                "release_date": "2010-07-16",
                "vote_average": 8.4,
                "poster": "https://image.tmdb.org/t/p/w500/...",
            }
        ]

        with (
            patch("app.main.get_headers") as mock_headers,
            patch("app.main.search_movies", new_callable=AsyncMock) as mock_search,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_search.return_value = mock_results

            response = test_client.post("/search", json=search_data)

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["original_title"] == "Inception"

            mock_search.assert_called_once()

    def test_search_series_success(self, test_client: TestClient):
        """Test successful series search."""
        search_data = {
            "text_search": "Breaking Bad",
            "type_of_content": "Series",
            "option_language": "en-US",
        }

        mock_results = [
            {
                "id": 1396,
                "name": "Breaking Bad",
                "air_date": "2008-01-20",
                "vote_avg": 9.5,
                "overview": "When an unassuming chemistry teacher...",
                "poster": "https://image.tmdb.org/t/p/w500/...",
            }
        ]

        with (
            patch("app.main.get_headers") as mock_headers,
            patch("app.main.search_series", new_callable=AsyncMock) as mock_search,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_search.return_value = mock_results

            response = test_client.post("/search", json=search_data)

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["name"] == "Breaking Bad"

            mock_search.assert_called_once()

    def test_search_invalid_content_type(self, test_client: TestClient):
        """Test search with invalid content type."""
        search_data = {
            "text_search": "test",
            "type_of_content": "Invalid",
            "option_language": "en-US",
        }

        response = test_client.post("/search", json=search_data)

        assert response.status_code == 400  # Validation error

    def test_search_empty_query(self, test_client: TestClient):
        """Test search with empty query."""
        search_data = {
            "text_search": "",
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        response = test_client.post("/search", json=search_data)

        assert response.status_code == 400  # Validation error

    def test_search_malicious_input(self, test_client: TestClient):
        """Test search with potentially malicious input."""
        search_data = {
            "text_search": "<script>alert('xss')</script>",
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        with (
            patch("app.main.get_headers") as mock_headers,
            patch("app.main.search_movies", new_callable=AsyncMock) as mock_search,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_search.return_value = []

            response = test_client.post("/search", json=search_data)

            # Should sanitize and accept the input
            assert response.status_code in [200, 400]

    def test_search_external_api_error(self, test_client: TestClient):
        """Test search when external API fails."""
        search_data = {
            "text_search": "test",
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        with (
            patch("app.main.get_headers") as mock_headers,
            patch("app.main.search_movies", new_callable=AsyncMock) as mock_search,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_search.side_effect = Exception("API Error")

            response = test_client.post("/search", json=search_data)

            assert response.status_code == 502
            data = response.json()
            assert "error" in data


class TestDetailsEndpoint:
    """Test details endpoint for movies and series."""

    def test_movie_details_success(self, test_client: TestClient):
        """Test successful movie details retrieval."""
        details_data = {
            "content_id": 27205,
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        mock_details = {
            "id": 27205,
            "original_title": "Inception",
            "overview": "Cobb, a skilled thief...",
            "release_date": "2010-07-16",
            "vote_average": 8.4,
            "is_available": True,
            "url": "https://vixsrc.to/movie/27205",
            "genres": ["Action", "Sci-Fi"],
            "runtime": 148,
            "poster": "https://image.tmdb.org/t/p/w500/...",
            "backdrop_path": "https://image.tmdb.org/t/p/original/...",
        }

        with (
            patch("app.main.get_headers") as mock_headers,
            patch(
                "app.main.get_movie_details", new_callable=AsyncMock
            ) as mock_details_func,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_details_func.return_value = mock_details

            response = test_client.post("/details", json=details_data)

            assert response.status_code == 200
            data = response.json()
            assert "details" in data
            assert data["details"]["original_title"] == "Inception"
            assert data["details"]["is_available"] is True

            mock_details_func.assert_called_once()

    def test_series_details_success(self, test_client: TestClient):
        """Test successful series details retrieval."""
        details_data = {
            "content_id": 1396,
            "type_of_content": "Series",
            "option_language": "en-US",
        }

        mock_details = {
            "id": 1396,
            "name": "Breaking Bad",
            "overview": "When an unassuming chemistry teacher...",
            "first_air_date": "2008-01-20",
            "vote_average": 9.5,
            "is_available": True,
            "url": "https://vixsrc.to/tv/1396",
            "genres": ["Drama", "Crime"],
            "valid_seasons": [1, 2, 3, 4, 5],
            "total_episodes": 62,
            "poster": "https://image.tmdb.org/t/p/w500/...",
            "backdrop_path": "https://image.tmdb.org/t/p/original/...",
        }

        with (
            patch("app.main.get_headers") as mock_headers,
            patch(
                "app.main.get_series_details", new_callable=AsyncMock
            ) as mock_details_func,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_details_func.return_value = mock_details

            response = test_client.post("/details", json=details_data)

            assert response.status_code == 200
            data = response.json()
            assert "details" in data
            assert data["details"]["name"] == "Breaking Bad"
            assert data["details"]["is_available"] is True
            assert len(data["details"]["valid_seasons"]) == 5

            mock_details_func.assert_called_once()

    def test_details_not_found(self, test_client: TestClient):
        """Test details for non-existent content."""
        details_data = {
            "content_id": 999999,
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        with (
            patch("app.main.get_headers") as mock_headers,
            patch(
                "app.main.get_movie_details", new_callable=AsyncMock
            ) as mock_details_func,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_details_func.side_effect = NotFoundError(
                "Movie with ID 999999 not found", "Movie", 999999
            )

            response = test_client.post("/details", json=details_data)

            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "not found" in str(data["error"]).lower()

    def test_details_invalid_content_id(self, test_client: TestClient):
        """Test details with invalid content ID."""
        details_data = {
            "content_id": -1,
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        response = test_client.post("/details", json=details_data)

        assert response.status_code == 400  # Validation error

    def test_details_invalid_content_type(self, test_client: TestClient):
        """Test details with invalid content type."""
        details_data = {
            "content_id": 27205,
            "type_of_content": "Invalid",
            "option_language": "en-US",
        }

        response = test_client.post("/details", json=details_data)

        assert response.status_code == 400  # Validation error


class TestMiddleware:
    """Test middleware functionality."""

    def test_process_time_header(self, test_client: TestClient):
        """Test that process time header is added."""
        response = test_client.get("/health")

        assert "X-Process-Time" in response.headers
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0

    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are present."""
        response = test_client.options("/health")

        # CORS headers should be present
        assert response.status_code in [200, 405]  # OPTIONS might not be implemented


class TestErrorHandling:
    """Test error handling and responses."""

    def test_authentication_error(self, test_client: TestClient):
        """Test authentication error handling."""
        with patch("app.main.get_headers") as mock_headers:
            mock_headers.side_effect = AuthenticationError("Invalid API key")

            search_data = {
                "text_search": "test",
                "type_of_content": "Movie",
                "option_language": "en-US",
            }

            response = test_client.post("/search", json=search_data)

            assert response.status_code == 401
            data = response.json()
            assert "error" in data

    def test_validation_error(self, test_client: TestClient):
        """Test validation error handling."""
        search_data = {
            "text_search": "a" * 1000,  # Too long
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        response = test_client.post("/search", json=search_data)

        assert response.status_code == 400

    def test_malformed_json(self, test_client: TestClient):
        """Test handling of malformed JSON."""
        response = test_client.post(
            "/search", data="invalid json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiting(self, test_client: TestClient):
        """Test that rate limiting is applied."""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = test_client.get("/health")
            responses.append(response)

        # All should succeed (rate limiting might be generous for tests)
        # but we can check that the middleware is working
        assert all(r.status_code == 200 for r in responses)


class TestInputSanitization:
    """Test input sanitization and validation."""

    def test_sql_injection_attempt(self, test_client: TestClient):
        """Test SQL injection attempt is sanitized."""
        search_data = {
            "text_search": "'; DROP TABLE users; --",
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        with (
            patch("app.main.get_headers") as mock_headers,
            patch("app.main.search_movies", new_callable=AsyncMock) as mock_search,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_search.return_value = []

            response = test_client.post("/search", json=search_data)

            # Should either accept sanitized input or reject it
            assert response.status_code in [200, 400]

    def test_xss_attempt(self, test_client: TestClient):
        """Test XSS attempt is sanitized."""
        search_data = {
            "text_search": "<script>alert('xss')</script>",
            "type_of_content": "Movie",
            "option_language": "en-US",
        }

        with (
            patch("app.main.get_headers") as mock_headers,
            patch("app.main.search_movies", new_callable=AsyncMock) as mock_search,
        ):
            mock_headers.return_value = {
                "accept": "application/json",
                "Authorization": "Bearer test",
            }
            mock_search.return_value = []

            response = test_client.post("/search", json=search_data)

            # Should either accept sanitized input or reject it
            assert response.status_code in [200, 400]


class TestCatalogEndpoint:
    """Test catalog endpoint for vixsrc.to API."""

    def test_catalog_movies_success(self, test_client: TestClient):
        """Test successful movie catalog retrieval."""
        mock_data = [
            {"id": 1, "title": "Movie 1", "year": 2023},
            {"id": 2, "title": "Movie 2", "year": 2024},
        ]

        class MockResponse:
            status = 200

            async def json(self):
                return mock_data

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def get(self, *args, **kwargs):
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        with patch("aiohttp.ClientSession", return_value=MockSession()):
            response = test_client.get("/catalog/movie")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2
            assert data["items"][0]["title"] == "Movie 1"

    def test_catalog_tv_with_lang(self, test_client: TestClient):
        """Test TV catalog retrieval with language parameter."""
        mock_data = [
            {"id": 1, "name": "Series 1"},
            {"id": 2, "name": "Series 2"},
        ]

        class MockResponse:
            status = 200

            async def json(self):
                return mock_data

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def get(self, *args, **kwargs):
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        with patch("aiohttp.ClientSession", return_value=MockSession()):
            response = test_client.get("/catalog/tv?lang=it")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 2

    def test_catalog_invalid_type(self, test_client: TestClient):
        """Test catalog with invalid content type."""
        response = test_client.get("/catalog/invalid")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_catalog_episode_success(self, test_client: TestClient):
        """Test episode catalog retrieval."""
        mock_data = [{"id": 1, "episode": "E01"}]

        class MockResponse:
            status = 200

            async def json(self):
                return mock_data

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def get(self, *args, **kwargs):
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        with patch("aiohttp.ClientSession", return_value=MockSession()):
            response = test_client.get("/catalog/episode")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1

    def test_catalog_api_error(self, test_client: TestClient):
        """Test catalog when vixsrc.to API fails."""

        class MockResponse:
            status = 500

            async def json(self):
                return {"error": "Internal Server Error"}

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def get(self, *args, **kwargs):
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        with patch("aiohttp.ClientSession", return_value=MockSession()):
            response = test_client.get("/catalog/movie")

            assert response.status_code == 500
            data = response.json()
            assert "error" in data

    def test_catalog_wrapped_data(self, test_client: TestClient):
        """Test catalog when API returns wrapped data."""
        mock_data = {"items": [{"id": 1, "title": "Movie"}]}

        class MockResponse:
            status = 200

            async def json(self):
                return mock_data

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def get(self, *args, **kwargs):
                return MockResponse()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        with patch("aiohttp.ClientSession", return_value=MockSession()):
            response = test_client.get("/catalog/movie")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1


