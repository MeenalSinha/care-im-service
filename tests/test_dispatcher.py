import pytest
import unittest.mock
from app.application.dispatcher import IntentDispatcher
from app.clients.care_api import CareAPIClient

@pytest.fixture
def mock_api_client():
    """Mock for the CARE API Client."""
    return unittest.mock.create_autospec(CareAPIClient)

@pytest.fixture
def dispatcher(mock_api_client):
    """Dispatcher instance with mocked API client."""
    return IntentDispatcher(whatsapp_id="919876543210", message_body="/hi", api_client=mock_api_client)

def test_dispatcher_start(dispatcher):
    """Verifies that /hi triggers the start intent."""
    response = dispatcher.dispatch()
    assert "Welcome to CARE" in response
    assert "/login" in response

def test_dispatcher_unknown_command(dispatcher):
    """Verifies handling of unknown commands."""
    dispatcher.message = "/unknown"
    response = dispatcher.dispatch()
    assert "I'm sorry, I don't understand" in response
    assert "/help" in response

def test_dispatcher_login_state_transition(dispatcher):
    """Verifies that /login transitions the dispatcher into the AWAITING_PHONE state."""
    with unittest.mock.patch("app.application.dispatcher.r") as mock_redis:
        dispatcher.message = "/login"
        response = dispatcher.dispatch()
        
        assert "Please enter your registered phone number" in response
        # Ensure state was set in Redis
        assert mock_redis.set.called
        args, kwargs = mock_redis.set.call_args
        assert "AWAITING_PHONE" in args[1]
