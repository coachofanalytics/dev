from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.core.domain.auth.auth import Credentials
from app.core.domain.auth.auth_service import AuthService
from app.core.domain.auth.exceptions import AuthenticationError, InvalidCredentialsError
from app.schemas.auth import TokenResponse, LoginRequest
from app.core.deps import get_auth_service

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    API endpoint for user login.
    Connects the API layer to the authentication domain logic.
    """
    try:
        # Convert API request to domain model
        credentials = Credentials(email=login_data.email, password=login_data.password)

        # Use domain service to handle authentication
        user, tokens = auth_service.authenticate(credentials)

        # Convert domain response to API response
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_at=tokens.expires_at,
        )

    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    API endpoint for refreshing access tokens.
    Connects the API layer to the authentication domain logic.
    """
    try:
        # Use domain service to handle token refresh
        tokens = auth_service.refresh_token(refresh_token)

        # Convert domain response to API response
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_at=tokens.expires_at,
        )

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
