import requests
import logging
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

class CareAPIError(Exception):
    """Base exception for CARE API errors."""
    def __init__(self, message: str, status_code: int = None, details: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

class CareAPIClient:
    """
    Dedicated Client for CARE Backend Communication.
    Handles authentication, error logging, and domain mapping.
    """
    def __init__(self, base_url: str = settings.CARE_API_BASE_URL, api_key: str = settings.CARE_API_KEY):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Api-Key {self.api_key}"})

    def _request(self, method: str, path: str, token: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Centralized request handler with error management."""
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
        
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            response = self.session.request(method, url, headers=headers, **kwargs)
            logger.debug(f"CARE API {method} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                self._handle_error(response)
                
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error communicating with CARE: {str(e)}")
            raise CareAPIError(f"Failed to connect to CARE: {str(e)}")

    def _handle_error(self, response: requests.Response):
        """Map HTTP errors to specific CareAPIError instances."""
        try:
            error_data = response.json()
        except:
            error_data = response.text
            
        msg = f"CARE API Error: {response.status_code} - {error_data}"
        logger.error(msg)
        raise CareAPIError(msg, status_code=response.status_code, details=error_data)

    # --- Authentication Methods ---

    def request_otp(self, phone_number: str) -> Dict[str, Any]:
        """Request an OTP for the given phone number."""
        return self._request("POST", "auth/otp/", json={"phone_number": phone_number})

    def login_with_otp(self, phone_number: str, otp: str) -> str:
        """Verify OTP and return the access token."""
        data = self._request("POST", "auth/login/", json={"phone_number": phone_number, "otp": otp})
        return data.get("access")

    def get_user_me(self, token: str) -> Dict[str, Any]:
        """Fetch current user profile data."""
        return self._request("GET", "users/me/", token=token)

    # --- Domain Resources ---

    def list_medications(self, token: str, status: str = "active") -> List[Dict[str, Any]]:
        """Fetch list of medications for the current user."""
        data = self._request("GET", "medication/", token=token, params={"status": status})
        return data.get("results", []) if isinstance(data, dict) else data

    def list_encounters(self, token: str) -> List[Dict[str, Any]]:
        """Fetch list of clinical encounters for the patient."""
        data = self._request("GET", "encounter/", token=token)
        return data.get("results", []) if isinstance(data, dict) else data

    def list_facility_assets(self, token: str, facility_id: str) -> List[Dict[str, Any]]:
        """Fetch assets for a specific facility (Staff Only)."""
        data = self._request("GET", "asset/", token=token, params={"facility": facility_id})
        return data.get("results", []) if isinstance(data, dict) else data
