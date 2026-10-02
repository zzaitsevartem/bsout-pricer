from fastapi.middleware.cors import CORSMiddleware

from src.main import app


def test_cors_allows_only_api_methods_and_headers():
    cors = next(
        middleware
        for middleware in app.user_middleware
        if middleware.cls is CORSMiddleware
    )

    assert set(cors.kwargs["allow_methods"]) == {
        "GET",
        "POST",
        "PATCH",
        "DELETE",
    }
    assert set(cors.kwargs["allow_headers"]) == {
        "Accept",
        "Authorization",
        "Content-Type",
    }
    assert "*" not in cors.kwargs["allow_methods"]
    assert "*" not in cors.kwargs["allow_headers"]
