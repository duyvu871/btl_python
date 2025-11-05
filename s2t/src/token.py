import logging

from fastapi import Depends, status, HTTPException
from src.grpc.auth_client import AuthGRPCClient, get_auth_client

logger = logging.getLogger(__name__)

async def verify_token(
    token: str,
    client: AuthGRPCClient = Depends(get_auth_client),
) -> dict:
    """
    Dependency to verify and extract user info from token.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        result = await client.validate_token(token, use_retry=True)

        if not result["is_valid"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify token",
        )
