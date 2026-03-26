import requests
import logging

logger = logging.getLogger(__name__)

class CareAPIClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Api-Key {self.api_key}"})

    def request_otp(self, phone_number):
        """
        Request an OTP for the given phone number from CARE backend.
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/otp/",
            json={"phone_number": phone_number}
        )
        return response.status_code == 200, response.json()

    def login_with_otp(self, phone_number, otp):
        """
        Verify OTP and get a JWT/Session token for the user.
        """
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login/",
            json={"phone_number": phone_number, "otp": otp}
        )
        if response.status_code == 200:
            return response.json().get("access") # Return JWT access token
        return None

    def get_user_profile(self, token):
        """
        Get current user profile using the token.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.get(f"{self.base_url}/api/v1/users/me/", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

    def get_medications(self, token):
        """
        Get active medications for the authenticated user.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.get(f"{self.base_url}/api/v1/medication/", headers=headers, params={"status": "active"})
        if response.status_code == 200:
            return response.json()
        return []

    def get_encounters(self, token):
        """
        Get recent encounters for the authenticated user.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.get(f"{self.base_url}/api/v1/encounter/", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []

    def get_assets(self, token, facility_id):
        """
        Get assets for a specific facility.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = self.session.get(f"{self.base_url}/api/v1/asset/", headers=headers, params={"facility": facility_id})
        if response.status_code == 200:
            return response.json()
        return []
