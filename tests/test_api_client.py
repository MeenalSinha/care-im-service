import pytest
import requests_mock
from app.clients.care_api import CareAPIClient, CareAPIError

@pytest.fixture
def api_client():
    return CareAPIClient(base_url="https://mock.care.api")

def test_request_otp_success(api_client):
    """Verifies that request_otp calls the correct endpoint."""
    with requests_mock.Mocker() as m:
        m.post("https://mock.care.api/api/v1/auth/otp/", json={"status": "OK"}, status_code=200)
        
        result = api_client.request_otp("+919000000000")
        assert result == {"status": "OK"}
        assert m.called

def test_request_otp_failure(api_client):
    """Verifies that CareAPIError is raised on 400 response."""
    with requests_mock.Mocker() as m:
        m.post("https://mock.care.api/api/v1/auth/otp/", json={"detail": "Invalid phone"}, status_code=400)
        
        with pytest.raises(CareAPIError) as excinfo:
            api_client.request_otp("+91")
        
        assert excinfo.value.status_code == 400
        assert "Invalid phone" in str(excinfo.value.details)

def test_list_medications_with_token(api_client):
    """Verifies that session token is correctly attached to list_medications."""
    token = "fake-jwt-token"
    mock_response = {"results": [{"medication": {"display": "Aspirin"}}]}
    
    with requests_mock.Mocker() as m:
        m.get("https://mock.care.api/api/v1/medication/", json=mock_response, status_code=200)
        
        result = api_client.list_medications(token=token)
        
        assert len(result) == 1
        assert result[0]["medication"]["display"] == "Aspirin"
        assert m.request_history[0].headers["Authorization"] == f"Bearer {token}"
