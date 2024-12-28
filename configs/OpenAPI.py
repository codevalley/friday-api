"""OpenAPI configuration module."""

from fastapi import FastAPI
from fastapi.security import HTTPBearer

from configs.Environment import get_environment_variables
from metadata.Tags import Tags


# Bearer token security scheme
bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT token obtained from /v1/auth/token using your API key",
    auto_error=False,  # Make authentication optional
)

# Instance to use in FastAPI dependencies
security = bearer_scheme


def configure_openapi(app: FastAPI) -> None:
    """Configure OpenAPI settings for the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    env = get_environment_variables()

    app.title = env.APP_NAME
    app.version = env.API_VERSION
    app.openapi_tags = Tags
    app.openapi_url = "/openapi.json"
    app.docs_url = "/docs"
    app.redoc_url = "/redoc"
