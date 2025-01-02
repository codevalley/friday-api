"""Custom HTTP Bearer authentication implementation."""

from fastapi import HTTPException
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)
from typing import Optional
from starlette.requests import Request


class CustomHTTPBearer(HTTPBearer):
    """Custom HTTP Bearer authentication that returns appropriate status codes.

    - 401 Unauthorized: Missing or invalid token
    - 403 Forbidden: Valid token but insufficient permissions
    """

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        """Process the authentication credentials.

        Args:
            request: The incoming request.

        Returns:
            The credentials if valid.

        Raises:
            HTTPException: 401 no/invalid token, 403 insufficient permissions.
        """
        try:
            return await super().__call__(request)
        except HTTPException as e:
            # Convert 403 to 401 for missing/invalid token scenarios
            if e.status_code == 403:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "code": "UNAUTHORIZED",
                        "message": (
                            "Invalid or missing authentication token"
                        ),
                        "type": "AuthenticationError",
                    },
                )
            raise
