import logging
from app.services.care_api_client import CareAPIClient

logger = logging.getLogger(__name__)

class OTPAuthFlow:
    """
    Handles the high-level logic for OTP-based authentication.
    Orchestrates calls to the CARE API and manages the verification process.
    """
    def __init__(self, api_client: CareAPIClient):
        self.api_client = api_client

    def initiate_login(self, phone_number: str):
        """
        Signals CARE backend to send an OTP to the user.
        """
        logger.info(f"Initiating login for: {phone_number}")
        success, response = self.api_client.request_otp(phone_number)
        return success, response

    def complete_login(self, phone_number: str, otp: str):
        """
        Verifies the OTP and retrieves the session token.
        """
        logger.info(f"Completing login for: {phone_number}")
        token = self.api_client.login_with_otp(phone_number, otp)
        
        if not token:
            return None, "Invalid OTP or verification failed."
            
        user_profile = self.api_client.get_user_profile(token)
        if not user_profile:
            return None, "Failed to retrieve user profile after login."
            
        return {"token": token, "user": user_profile}, None
