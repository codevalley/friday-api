from fastapi.security import HTTPBearer

# Bearer token security scheme
bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT token obtained from /v1/auth/token using your API key",
    auto_error=False,  # Make authentication optional
)

# Instance to use in FastAPI dependencies
security = bearer_scheme
