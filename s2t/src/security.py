from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from langgraph_sdk.auth.exceptions import HTTPException

from src.grpc import get_auth_client, AuthGRPCClient

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_user_id(token: str = Depends(oauth2_scheme), auth_client: AuthGRPCClient = Depends(get_auth_client)) -> str:
    token_validation = await auth_client.validate_token(token)
    if not token_validation.is_valid or token_validation.expires_at is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token_validation.user_id


