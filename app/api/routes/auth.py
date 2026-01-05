"""Authentication API routes."""

import logging
from fastapi import APIRouter, HTTPException, status

from app.core.telegram_client import telegram_manager
from app.core.exceptions import (
    TelegramNotAuthenticatedError,
    TwoFactorAuthRequiredError,
    InvalidPhoneCodeError,
    InvalidPasswordError
)
from app.models.requests import (
    RequestCodeRequest,
    VerifyCodeRequest,
    Verify2FARequest
)
from app.models.responses import (
    CodeSentResponse,
    AuthSuccessResponse,
    TwoFactorRequiredResponse,
    AuthStatusResponse,
    SuccessResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/request-code",
    response_model=CodeSentResponse,
    summary="Request verification code",
    description="Send verification code to phone number via Telegram"
)
async def request_code(request: RequestCodeRequest):
    """
    Request verification code to be sent to the provided phone number.

    The code will be sent to the Telegram app associated with this phone number.
    Use the returned phone_code_hash in the verify-code endpoint.
    """
    try:
        phone_code_hash = await telegram_manager.send_code(request.phone)

        logger.info(f"Verification code sent to {request.phone}")

        return CodeSentResponse(
            phone_code_hash=phone_code_hash,
            message=f"Verification code sent to {request.phone}"
        )

    except TelegramNotAuthenticatedError as e:
        logger.error(f"Telegram not connected: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram client not connected. Please try again later."
        )

    except Exception as e:
        logger.error(f"Failed to send verification code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification code: {str(e)}"
        )


@router.post(
    "/verify-code",
    response_model=AuthSuccessResponse | TwoFactorRequiredResponse,
    summary="Verify phone code",
    description="Verify the code received in Telegram"
)
async def verify_code(request: VerifyCodeRequest):
    """
    Verify the code sent to your phone.

    If two-factor authentication is enabled, this will return
    two_factor_required=true and you'll need to call /verify-2fa.
    """
    try:
        await telegram_manager.sign_in(
            request.phone,
            request.code,
            request.phone_code_hash
        )

        # Get user info after successful sign in
        me = await telegram_manager.get_me()

        logger.info(f"Successfully authenticated user {me.id}")

        return AuthSuccessResponse(
            user_id=me.id,
            message="Authentication successful"
        )

    except TwoFactorAuthRequiredError:
        logger.info("Two-factor authentication required")
        return TwoFactorRequiredResponse()

    except InvalidPhoneCodeError:
        logger.warning("Invalid verification code provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check and try again."
        )

    except TelegramNotAuthenticatedError as e:
        logger.error(f"Telegram not connected: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram client not connected"
        )

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.post(
    "/verify-2fa",
    response_model=AuthSuccessResponse,
    summary="Verify 2FA password",
    description="Complete authentication with two-factor password"
)
async def verify_2fa(request: Verify2FARequest):
    """
    Complete authentication using two-factor authentication password.

    Use this endpoint after verify-code returns two_factor_required=true.
    """
    try:
        await telegram_manager.check_password(request.password)

        # Get user info
        me = await telegram_manager.get_me()

        logger.info(f"Successfully authenticated user {me.id} with 2FA")

        return AuthSuccessResponse(
            user_id=me.id,
            message="Two-factor authentication successful"
        )

    except InvalidPasswordError:
        logger.warning("Invalid 2FA password provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid two-factor authentication password"
        )

    except TelegramNotAuthenticatedError as e:
        logger.error(f"Telegram not connected: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram client not connected"
        )

    except Exception as e:
        logger.error(f"2FA verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"2FA verification failed: {str(e)}"
        )


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    summary="Get authentication status",
    description="Check if currently authenticated with Telegram"
)
async def get_auth_status():
    """
    Get current authentication status.

    Returns information about whether the user is authenticated
    and basic user details if authenticated.
    """
    try:
        is_connected = telegram_manager.is_connected()
        is_authorized = await telegram_manager.is_authorized()

        if not is_connected:
            return AuthStatusResponse(
                authenticated=False,
                user_id=None,
                username=None,
                phone=None
            )

        if not is_authorized:
            return AuthStatusResponse(
                authenticated=False,
                user_id=None,
                username=None,
                phone=None
            )

        # Get user info
        me = await telegram_manager.get_me()

        return AuthStatusResponse(
            authenticated=True,
            user_id=me.id,
            username=me.username,
            phone=me.phone_number
        )

    except Exception as e:
        logger.error(f"Failed to get auth status: {e}")
        return AuthStatusResponse(
            authenticated=False,
            user_id=None,
            username=None,
            phone=None
        )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Logout from Telegram",
    description="Invalidate current session and logout"
)
async def logout():
    """
    Logout from Telegram and invalidate the current session.

    This will require re-authentication to use the API again.
    """
    try:
        await telegram_manager.log_out()

        logger.info("Successfully logged out from Telegram")

        return SuccessResponse(
            message="Successfully logged out from Telegram"
        )

    except TelegramNotAuthenticatedError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )
